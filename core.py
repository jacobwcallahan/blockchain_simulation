class Node:
    def __init__(self, id=None, num_neighbors=float("inf")):
        self.neighbors = []
        self.max_neighbors = num_neighbors
        self.blockchain = []
        self.id = id

    def broadcast_update(self, block):
        """
        Broadcasts the block to all neighbors.
        """
        for neighbor in self.neighbors:
            neighbor.receive_block(block)

    def receive_block(self, block):
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
    def __init__(self, hashrate=1):
        self.hashrate = hashrate


class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
