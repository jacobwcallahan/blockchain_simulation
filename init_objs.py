import random
from core import Node, Miner, Wallet


def init_nodes(env, num_nodes, max_neighbors, blockchain):
    """
    Initializes the nodes for the simulation.
    """
    nodes = []

    # Create nodes
    for i in range(num_nodes):
        nodes.append(Node(env, id=i, num_neighbors=max_neighbors, ledger=[]))

    # Assign neighbors to each node
    for node in nodes:
        neighbors = min(
            node.max_neighbors, num_nodes - 1
        )  # Ensure we don't exceed available nodes
        possible_neighbors = [x for x in range(0, num_nodes) if x != node.id]
        neighbor_ids = random.sample(possible_neighbors, neighbors)

        node.neighbors = [nodes[x] for x in neighbor_ids]

    # Ensures each neighbor is added to the other node's neighbors
    for node in nodes:
        for neighbor in node.neighbors:
            if node not in neighbor.neighbors:
                neighbor.neighbors.append(node)

    return nodes


def init_wallets(num_wallets):
    wallets = []
    for i in range(num_wallets):
        wallets.append(Wallet(id=i))
    return wallets


def init_miners(env, num_miners, hashrate, nodes, wallets, random_hashrate=False):
    """
    Initializes the miners for the simulation.
    """
    miners = []
    temp_hashrate = hashrate

    miner_wallets = random.sample(
        wallets,
        num_miners,
    )

    if random_hashrate:
        for i in range(num_miners):

            # Assign a random node to each miner
            node = random.choice(nodes)

            # If random hashrate is True, assign a random hashrate to the miner
            if temp_hashrate > 0:

                miners.append(
                    Miner(
                        env,
                        id=i,
                        node=node,
                        hashrate=random.randint(0, temp_hashrate),
                        wallet=miner_wallets[i],
                    )
                )
                temp_hashrate -= miners[-1].hashrate
            else:
                miners.append(
                    Miner(
                        env,
                        id=i,
                        node=node,
                        hashrate=0,
                        wallet=miner_wallets[i],
                    )
                )
    else:

        for i in range(num_miners):
            node = random.choice(nodes)
            miners.append(
                Miner(
                    env,
                    id=i,
                    node=node,
                    hashrate=hashrate,
                    wallet=miner_wallets[i],
                )
            )

    return miners
