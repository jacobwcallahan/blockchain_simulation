import random
import time
import math
import gc


class Node:
    """
    A node in the network. This is a single node that can communicate with other nodes.

    It stores the neighbors of the node, the ledger of the node, the total number of IO requests, the bandwidth, the broadcast times, the latency, and the id of the node.

    Attributes:
        env: The environment.
        neighbors: The neighbors of the node. This is a list of Node Objects that the node can communicate with.
        max_neighbors: The maximum number of neighbors the node can have.
        id: The id of the node.
        ledger: The ledger of the node. This is a list of Block Objects that the node has added to its ledger.
    """

    def __init__(
        self,
        env,
        bandwidth=float("inf"),
        id=None,
        num_neighbors=float("inf"),
        latency=0,
    ):
        """
        Initializes a node.
        """
        self.env = env
        self.neighbors = []
        self.max_neighbors = num_neighbors
        self.id = id
        self.ledger = []
        self.ledger_size = 0
        self.total_io_requests = 0
        self.network_usage = 0
        self.bandwidth = bandwidth
        self.broadcast_times = []
        self.latency = latency
        self.last_block = None

    def mine_block(self, block):
        """
        Mines a block and adds it to the blockchain. As well as broadcasts the block to all neighbors.
        """
        self.ledger.append(block.block_id)
        self.ledger_size += 1
        self.last_block = block
        yield self.env.process(self.broadcast_update(block))
        self.resize_ledger()

    def broadcast_update(self, block, latency=0):
        """
        Broadcasts the block to all neighbors.

        Args:
            block (Block): The block to broadcast.
            latency (float): The latency of the block. Optional, defaults to 0.
        """

        # If the bandwidth is not infinite, the broadcast time is the size of the block divided by the bandwidth
        if self.bandwidth != float("inf"):
            broadcast_time = block.size / self.bandwidth
        else:
            broadcast_time = 0

        if len(self.broadcast_times) < self.ledger_size:
            self.broadcast_times.append(0)

        for i in range(len(self.neighbors)):
            neighbor = self.neighbors[i]

            # Checks if neighbor already has the block
            if neighbor.last_block is not None:
                if neighbor.last_block == block:
                    continue

            self.total_io_requests += 1
            self.network_usage += block.size
            self.broadcast_times[-1] += latency + broadcast_time

            # If the latency is not 0, the block is received with the latency of the node + the broadcast time
            if latency != 0:
                yield self.env.process(
                    neighbor.receive_block(block, self.latency + broadcast_time)
                )
            else:
                yield self.env.process(
                    neighbor.receive_block(block, latency=self.latency)
                )

    def receive_block(self, block, latency=0):
        """
        Receives a block from a neighbor and adds it to the blockchain if it's valid.
        If the block is the same as the last block in the blockchain, it does nothing.
        If the block has an invalid ID, the last block in the blockchain is replaced with the new block if it's newer.
        (Although this shouldn't happen, it's caught in broadcast_update)

        Args:
            block (Block): The block to receive.
            latency (float): The latency of the block. Optional, defaults to 0.
        """

        self.ledger.append(block.block_id)
        self.ledger_size += 1

        self.total_io_requests += 1

        yield self.env.timeout(latency + block.size / self.bandwidth)
        if len(self.broadcast_times) < self.ledger_size:
            self.broadcast_times.append(0)

        self.broadcast_times[-1] += latency + block.size / self.bandwidth

        yield self.env.process(self.broadcast_update(block, latency=self.latency))

        self.last_block = block

        self.resize_ledger()

    def resize_ledger(self):
        if len(self.ledger) > 1000000:
            old_ledger = self.ledger
            self.ledger = list(self.ledger[-500000:])
            del old_ledger
            gc.collect()

    def __eq__(self, other):
        if self.id == other.id:
            return True
        else:
            return False


class Miner:
    """
    A miner. This is a single miner that can mine blocks.

    It stores the hashrate of the miner and the wallet of the miner.

    Attributes:
        id: The id of the miner.
        env: The environment.
        hashrate: The hashrate of the miner.
        mine_time: The time it takes to mine a block.
        node: The node that the miner is on.
        wallet: The wallet of the miner.
    """

    def __init__(
        self,
        env,
        id=None,
        node=None,
        hashrate=None,
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

    def get_mine_time(self, difficulty):
        if self.node is None:
            raise ValueError("Miner has no node - set_node() not called")

        if self.hashrate == 0:
            self.mine_time = float("inf")
        else:

            self.mine_time = random.expovariate(self.hashrate / difficulty)

        return self.mine_time

    def win_block(self, block):
        yield self.env.process(self.node.mine_block(block))

    def __str__(self):
        return self.id

    def __repr__(self):
        return f"Miner(id={self.id}, hashrate={self.hashrate})"


class Transaction:
    """
    A transaction. This is a single transaction between two wallets.

    Attributes:
        env: The environment.
        amount: The amount of the transaction.
        receiver: The receiver of the transaction.
    """

    def __init__(self, env, amount, receiver, sender=None):
        self.size = 256
        if amount is None:
            raise ValueError("Amount cannot be None")

        if amount <= 0:
            print(amount)
            raise ValueError("Amount must be greater than 0")

        if sender == receiver:
            raise ValueError("Sender and receiver cannot be the same")

        if sender is not None and amount > sender.balance:
            raise ValueError("Sender does not have enough balance")

        self.creation_time = env.now
        self.proceess_time = None
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.type = "Reward" if sender is None else "Transaction"

        # This ensures that the sender's balance is subtracted before the transaction is added to the blockchain
        # This is to prevent the sender from spending more than they have
        self.subtract_balance()

    def subtract_balance(self):
        if self.sender is not None:
            self.sender.add_transaction(self)

    def add_balance(self):
        if self.receiver is not None:
            self.receiver.add_transaction(self)

    def __eq__(self, other):
        if (
            self.creation_time == other.creation_time
            and self.proceess_time == other.proceess_time
            and self.sender == other.sender
            and self.receiver == other.receiver
            and self.amount == other.amount
            and self.type == other.type
        ):
            return True
        else:
            return False

    def __str__(self):
        return f"Transaction(sender={self.sender}, receiver={self.receiver}, amount={self.amount}, type={self.type})"

    def __repr__(self):
        return f"Transaction(sender={self.sender}, receiver={self.receiver}, amount={self.amount}, type={self.type})"


class Wallet:
    """
    A wallet. This is a single wallet that can send and receive transactions.

    It stores the transactions that the wallet has sent and received.

    As well it stores the balance of the wallet.

    Attributes:
        id: The id of the wallet.
        tx_out: The transactions that the wallet has sent.
    """

    def __init__(self, id):
        self.id = id
        self.tx_out = 0
        self.tx_in = 0
        self.balance = 0

    def add_transaction(self, transaction):

        if transaction.receiver.id == self.id:
            self.tx_in += 1
            self.balance += transaction.amount
        else:
            self.tx_out += 1
            self.balance -= transaction.amount

    def __str__(self):
        return f"Wallet(id={self.id}, balance={self.balance})"

    def __repr__(self):
        return f"Wallet(id={self.id}, balance={self.balance})"


class Block:
    """
    A block in the blockchain. This is the unit of work that is mined by a miner.
    It stores the transactions that have been added to the blockchain.

    The block is created by the BlockChain class and is added to the blockchain by the BlockChain class.

    Attributes:
        header: The header of the block.
        block_id: The id of the block.
        timestamp: The timestamp of the block.
        env: The environment.
        time_since_last_block: The time since the last block.
        transaction_count: The number of transactions in the block.
        size: The size of the block.
        blocksize: The size of the blocks in the blockchain.
        transactions: The transactions in the block.
    """

    def __init__(self, env, id, blocksize):
        self.header = None
        self.block_id = id
        self.timestamp = env.now
        self.env = env
        self.time_since_last_block = None
        self.transaction_count = 0

        # Base size taken up by the header
        self.size = 1024
        self.blocksize = blocksize
        self.transactions = []
        self.full = False
        self.fees = 0

    def add_transaction(self, transaction):
        """
        Adds a transaction to the block. Checks if the block is full and raises an error if it is.

        Args:
            transaction (Transaction): The transaction to add.
        """

        if self.full:
            raise ValueError("Block is full - transaction not added")

        transaction.proceess_time = self.env.now
        self.transactions.append(transaction)
        self.transaction_count += 1
        self.size += transaction.size

        # +1 because the block size is the number of transactions + 1 reward transaction
        if len(self.transactions) >= self.blocksize + 1:
            self.full = True

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
    """
    The Blockchain. This handles the creation of blocks and the addition of transactions to the blockchain.
    It also handles the creation of rewards and the addition of transactions to the blockchain.


    Attributes:
        env: The environment.
        blocks: The blocks in the blockchain.
        total_transactions: The total number of transactions in the blockchain.
        blocksize: The size of the blocks in the blockchain.
        coins: The total number of coins in the blockchain.
        reward: The reward for mining a block.
        halving: The number of blocks until the reward is halved.
        fee: The fee for each transaction as a percentage of the transaction amount.
        tx_pool: The queue of transactions to be added to the blockchain.
        current_block: The current block being mined.
        stop_process: Whether the process should stop.
        total_fees: The total fees in the blockchain.
    """

    def __init__(self, env, blocksize, reward, halving, fee=0):
        self.env = env
        self.blocks = []
        self.total_blocks = 0
        self.total_transactions = 0
        self.blocksize = blocksize
        self.coins = 0
        self.reward = reward

        self.halving = halving
        self.fee = fee
        self.total_fees = 0
        self.tx_pool = []
        self.stop_process = False

        self.create_block(env)

    def create_reward(self):
        """
        Creates the reward for the block. Based on the halving and the fees.

        Returns:
            float: The reward for the block.
        """
        if self.halving == 0:
            return self.reward

        reward = (
            self.reward * (0.5 ** (self.total_blocks // self.halving))
        ) + self.current_block.fees
        return reward

    def finalize_block(self):
        """Finalizes the current block and adds it to the blockchain. Also adds the reward to the miner's wallet.
        Also adds the transactions to the block from the transaction queue until the block is full.

        Args:
            winning_miner (Miner): The miner that won the block.
        """

        block = self.current_block

        # Adds transactions to the block from the transaction queue until the block is full
        if len(self.tx_pool) != 0:
            while not block.full:
                transaction = self.tx_pool.pop(0)

                # If the transaction is a transaction and not a reward, add the fee to the block fees
                if transaction.type == "Transaction":
                    fee = transaction.amount * self.fee

                    transaction.amount -= fee

                    if transaction.amount < 0:
                        raise ValueError(
                            "Transaction amount is less than 0. This should not happen."
                        )

                    self.current_block.fees += fee

                    self.total_fees += fee

                # Processes the receiver of transaction
                transaction.add_balance()
                block.add_transaction(transaction)

                if len(self.tx_pool) == 0:
                    break

        self.blocks.append(self.current_block)

        self.total_transactions += block.transaction_count

    def create_block(self, env, winning_miner=None):
        """
        Creates a new block with id equal to the length of the blockchain.
        Also adds the reward transaction to the transaction pool.

        Miner is only not provided if the block is the first block in the blockchain.

        Args:
            env (simpy.Environment): The environment.
            winning_miner (Miner, optional): The miner that won the block. Defaults to None.
        """
        block = Block(env, id=self.total_blocks, blocksize=self.blocksize)
        block.transactions = []
        block.timestamp = env.now

        block.time_since_last_block = (
            env.now - self.get_last_block().timestamp if self.blocks else 0
        )

        if winning_miner:
            reward_amount = self.create_reward()
            reward_transaction = Transaction(
                self.env,
                amount=reward_amount,
                receiver=winning_miner.wallet,
            )
            self.coins += reward_amount
            self.tx_pool.insert(0, reward_transaction)

        self.current_block = block
        self.total_blocks += 1

        # Keeps the blockchain to 500,000 blocks
        # This prevents memory issues with the blockchain
        if len(self.blocks) > 1000000:

            # Clear internal data of old blocks
            for old_block in self.blocks[:-500000]:
                old_block.__dict__.clear()

            # Now slice and reallocate the list
            self.blocks = list(self.blocks[-500000:])

            gc.collect()

    def add_transaction(self, transaction):
        self.tx_pool.append(transaction)

    def get_current_block(self):
        return self.current_block

    def get_last_block(self):
        return self.blocks[-1]

    def __repr__(self):
        block_ids = [block.block_id for block in self.blocks]
        block_timestamps = [block.timestamp for block in self.blocks]
        block_num_transactions = [block.transaction_count for block in self.blocks]
        return f"BlockChain(blocks={block_ids}, timestamps={block_timestamps}, transaction_counts={block_num_transactions})"
