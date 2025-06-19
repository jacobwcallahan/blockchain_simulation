import random


class Node:
    def __init__(self, env, id=None, num_neighbors=float("inf")):
        self.env = env
        self.neighbors = []
        self.max_neighbors = num_neighbors
        self.blockchain = []
        self.id = id

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
                neighbor.receive_block(block, latency[i] + broadcast_time)
            else:
                neighbor.receive_block(block)

    def receive_block(self, block, latency=0):
        """
        Receives a block from a neighbor and adds it to the blockchain if it's valid.
        If the block is the same as the last block in the blockchain, it does nothing.
        If the block has an invalid ID, the last block in the blockchain is replaced with the new block if it's newer.
        """

        if self.blockchain:
            last_block = self.blockchain[-1]
        else:
            self.blockchain.append(block)
            self.broadcast_update(block)
            return

        # Checks if block has valid ID
        if block.block_id > last_block.block_id:
            self.blockchain.append(block)
            self.broadcast_update()

        # Notes its the same block and doesn't add it to the blockchain
        elif block.block_id == last_block.block_id:
            return
        else:
            # If block has invalid ID, the last block in blockchain is replaced with the new block if it's newer

            yield self.env.timeout(latency)

            self.blockchain[-1] = (
                block if block.timestamp > last_block.timestamp else last_block
            )

        self.broadcast_update(self.blockchain[-1])

    def __eq__(self, other):
        # Checks if the block is the same as another block
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


class Block:
    def __init__(self):
        self.header = None
        self.transactions = None
        self.block_id = None
        self.timestamp = None
        self.time_since_last_block = None
        self.transaction_count = None
        self.size = None


class Miner:
    def __init__(
        self,
        env,
        id=None,
        hashrate=1,
    ):
        self.id = id
        self.env = env
        self.hashrate = hashrate
        self.mine_time = None

    def get_mine_time(self, n):
        if self.hashrate == 0:
            self.mine_time = float("inf")
        else:
            self.mine_time = min(random.sample(range(0, n), self.hashrate))
        return self.mine_time

    def __str__(self):
        return self.id

    def __repr__(self):
        return f"Miner(id={self.id}, hashrate={self.hashrate})"


class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
