import random
import time
import math


class Node:
    """
    A node in the network.

    Attributes:
        env: The environment.
        neighbors: The neighbors of the node. This is a list of Node Objects that the node can communicate with.
        max_neighbors: The maximum number of neighbors the node can have.
        id: The id of the node.
        ledger: The ledger of the node. This is a list of Block Objects that the node has added to its ledger.
    """

    def __init__(self, env, ledger, id=None, num_neighbors=float("inf")):
        """
        Initializes a node.
        """
        self.env = env
        self.neighbors = []
        self.max_neighbors = num_neighbors
        self.id = id
        self.ledger = []

    def mine_block(self, block):
        """
        Mines a block and adds it to the blockchain.
        """
        self.ledger.append(block)
        self.broadcast_update(block)

    def broadcast_update(self, block, latency=None, bandwidth=float("inf")):
        """
        Broadcasts the block to all neighbors.
        """

        if bandwidth != float("inf"):
            broadcast_time = block.size / bandwidth
        else:
            broadcast_time = 0

        for i in range(len(self.neighbors)):
            neighbor = self.neighbors[i]

            if latency is not None:
                yield self.env.process(
                    neighbor.receive_block(block, latency[i] + broadcast_time)
                )
            else:
                yield self.env.process(neighbor.receive_block(block))

    def receive_block(self, block, latency=0):
        """
        Receives a block from a neighbor and adds it to the blockchain if it's valid.
        If the block is the same as the last block in the blockchain, it does nothing.
        If the block has an invalid ID, the last block in the blockchain is replaced with the new block if it's newer.
        """

        yield self.env.timeout(latency)

        print(f"Node {self.id} received block {block.block_id}")

        # Check if ledger is empty
        if len(self.ledger) == 0:
            self.ledger.append(block)
            return

        last_block = self.ledger[-1]

        # If the block has a valid ID, it is added to the blockchain
        if last_block.block_id < block.block_id:
            self.ledger.append(block)

        # Notes its the same block and doesn't add it to the blockchain
        # This is for the case where the block is the same as the last block in the blockchain
        elif block == last_block:
            return
        else:
            # if blocks are not equal and there is an id issue, the last block in the blockchain is replaced with the new block if it's newer
            self.ledger[-1] = (
                block if block.timestamp > last_block.timestamp else last_block
            )

        yield self.env.process(self.broadcast_update(self.ledger[-1]))

    def __eq__(self, other):
        if self.id == other.id:
            return True
        else:
            return False


class Miner:
    def __init__(
        self,
        env,
        id=None,
        node=None,
        hashrate=1,
        wallet=None,
    ):
        self.id = id
        self.env = env
        self.hashrate = hashrate
        self.mine_time = None
        self.node = node
        if wallet is None:
            self.wallet = Wallet(id=id)
        else:
            self.wallet = wallet

    def set_node(self, node: Node):
        self.node = node

    def get_node(self):
        return self.node

    def get_mine_time(self, n):
        if self.node is None:
            raise ValueError("Miner has no node - set_node() not called")

        if self.hashrate == 0:
            self.mine_time = float("inf")
        else:

            self.mine_time = random.randint(0, math.ceil(n / self.hashrate))

        return self.mine_time

    def win_block(self, block):
        self.node.mine_block(block)

    def __str__(self):
        return self.id

    def __repr__(self):
        return f"Miner(id={self.id}, hashrate={self.hashrate})"


class Transaction:
    def __init__(self, env, amount, receiver, sender=None):

        if sender == receiver:
            raise ValueError("Sender and receiver cannot be the same")

        if sender is not None and amount > sender.balance:
            raise ValueError("Sender does not have enough balance")

        self.timestamp = env.now
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.type = "Reward" if sender is None else "Transaction"

        self.execute()

    def execute(self):
        if self.sender is not None:
            self.sender.subtract_balance(self)
        self.receiver.add_balance(self)

    def __str__(self):
        return f"Transaction(sender={self.sender}, receiver={self.receiver}, amount={self.amount}, type={self.type})"

    def __repr__(self):
        return f"Transaction(sender={self.sender}, receiver={self.receiver}, amount={self.amount}, type={self.type})"


class Wallet:
    def __init__(self, id):
        self.id = id
        self.transactions = []
        self.balance = 0

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def add_balance(self, transaction):
        self.balance += transaction.amount

    def subtract_balance(self, transaction):
        self.balance -= transaction.amount

    def __str__(self):
        return f"Wallet(id={self.id}, balance={self.balance})"

    def __repr__(self):
        return f"Wallet(id={self.id}, balance={self.balance})"


class Block:
    def __init__(self, env, id):
        self.header = None
        self.transactions = None
        self.block_id = id
        self.timestamp = env.now
        self.time_since_last_block = None
        self.transaction_count = 0
        self.size = 0
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        self.transaction_count += 1
        self.size += 256  # TODO: Add the size of the transaction

    def __repr__(self):
        return f"Block(id={self.block_id}, timestamp={self.timestamp}, time_since_last_block={self.time_since_last_block}, transaction_count={self.transaction_count}, size={self.size})"

    def __eq__(self, other):
        if (
            self.block_id == other.block_id
            and self.timestamp == other.timestamp
            and self.time_since_last_block == other.time_since_last_block
            and self.transaction_count == other.transaction_count
            and self.size == other.size
        ):
            return True
        else:
            return False


class BlockChain:
    def __init__(self, env):
        self.env = env
        self.blocks = []
        self.total_transactions = 0
        self.current_block = self.create_block(env)
        self.coins = 0

    def finalize_block(self):
        """
        Finalizes the current block and adds it to the blockchain.
        """

        self.blocks.append(self.current_block)
        self.current_block = self.create_block(self.env)
        self.pool = 0

    def create_block(self, env):
        """
        Creates and returns new block with id equal to the length of the blockchain.
        """
        block = Block(env, id=len(self.blocks))
        block.header = {}
        block.transactions = []
        block.timestamp = env.now
        block.time_since_last_block = (
            env.now - self.get_last_block().timestamp if self.blocks else 0
        )
        block.transaction_count = 0
        block.size = 0

        return block

    def add_transaction(self, transaction):
        self.total_transactions += 1
        self.current_block.add_transaction(transaction)

    def get_current_block(self):
        return self.current_block

    def get_last_block(self):
        return self.blocks[-1]

    def __eq__(self, other):
        for i in range(len(self.blocks)):
            if self.blocks[i] != other.blocks[i]:
                return False
        return True

    def __repr__(self):
        block_ids = [block.block_id for block in self.blocks]
        block_timestamps = [block.timestamp for block in self.blocks]
        block_num_transactions = [block.transaction_count for block in self.blocks]
        block_sizes = [block.size for block in self.blocks]
        return f"BlockChain(blocks={block_ids}, timestamps={block_timestamps}, transaction_counts={block_num_transactions})"
