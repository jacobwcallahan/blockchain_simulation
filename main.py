import simpy
from core import Node, Block, Miner
import random
import math


def create_nodes(env, num_nodes):
    nodes = []
    for i in range(num_nodes):
        nodes.append(Node(env, id=i, num_neighbors=3))

    for node in nodes:
        neighbors = node.max_neighbors
        possible_neighbors = [x for x in range(0, num_nodes) if x != node.id]
        neighbor_ids = random.sample(possible_neighbors, neighbors)
        node.neighbors = [nodes[x] for x in neighbor_ids]
        print(f"Node {node.id} | Neighbors: {[x.id for x in node.neighbors]}")

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


def create_miners(env, num_miners, total_hashrate, random_hashrate=False):
    miners = []
    temp_hashrate = total_hashrate
    for i in range(num_miners):
        if random_hashrate:
            if temp_hashrate > 0:
                miners.append(
                    Miner(env, id=i, hashrate=random.randint(0, temp_hashrate))
                )
                temp_hashrate -= miners[-1].hashrate
            else:
                miners.append(Miner(env, id=i, hashrate=0))
        else:
            miners.append(Miner(env, id=i, hashrate=int(total_hashrate / num_miners)))

    return miners


def get_difficulty(expected_time_per_block, hashrate):
    return 1 / (math.log(expected_time_per_block) / hashrate)


def main():
    env = simpy.Environment()
    total_hashrate = 10000
    miners = create_miners(env, 10, total_hashrate, random_hashrate=True)
    expected_time_per_block = 100
    difficulty = get_difficulty(expected_time_per_block, total_hashrate)
    print(f"Difficulty: {difficulty}")

    # expected_time_per_block = math.exp(total_hashrate / difficulty)
    n = expected_time_per_block * total_hashrate

    winning_times = []

    for i in range(1000):

        mine_times = []

        for miner in miners:
            miner.get_mine_time(n)
            mine_times.append(miner.mine_time)

        winning_times.append(min(mine_times))

    print(sum(winning_times) / len(winning_times))

    print(f"Expected time per block: {expected_time_per_block}")
    nodes = create_nodes(env, 10)


if __name__ == "__main__":
    main()
