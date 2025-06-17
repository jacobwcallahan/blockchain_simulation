import simpy
from core import Node, Block
from random import sample
import math


def create_nodes(num_nodes):
    nodes = []
    for i in range(num_nodes):
        nodes.append(Node(id=i, num_neighbors=3))

    for node in nodes:
        neighbors = node.max_neighbors
        possible_neighbors = [x for x in range(0, num_nodes) if x != node.id]
        node.neighbors = sample(possible_neighbors, neighbors)
        print(f"Node {node.id} | Neighbors: {node.neighbors}")

    return nodes


def create_block(env, nodes, blockchain):
    block = Block()
    block.header = {}
    block.transactions = []
    block.block_id = len(blockchain)
    block.timestamp = env.now
    block.time_since_last_block = (
        env.now - blockchain[-1].timestamp if blockchain else 0
    )
    block.transaction_count = 0
    block.size = 0

    return block


def main():
    env = simpy.Environment()
    difficulty = 4
    hashrate = 1
    expected_time_per_block = math.exp(hashrate / difficulty)
    nodes = create_nodes(10)


if __name__ == "__main__":
    main()
