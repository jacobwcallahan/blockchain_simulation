import simpy
from core import Node, Block, Miner, BlockChain, Transaction, Wallet
import random
import math
from init_objs import init_nodes, init_wallets, init_miners
from stats import Stats


def get_winning_miner(miners, difficulty):
    """
    Returns the miner with the shortest mining time.
    """

    mine_times = []

    for miner in miners:
        miner.get_mine_time(math.ceil(difficulty))
        mine_times.append(miner.mine_time)

    return miners[mine_times.index(min(mine_times))]


def mine_block(miners, difficulty):
    """
    Mines a block and alerts the winning miner.
    """

    # Get the winning miner
    winning_miner = get_winning_miner(miners, difficulty)

    # Wait for the winning miner to mine the block

    # Add the block to the blockchain

    return winning_miner


def make_random_transaction(env, blockchain, sender, receivers, amount=None):
    """
    Adds transactions to the block.
    """
    receiver = random.choice(receivers)

    # Ensures the sender has a balance > 0

    while sender == receiver:

        receiver = random.choice(receivers)

    if amount is None:

        amount = random.uniform(0, sender.balance)

        if amount > sender.balance:
            print(amount)
            print(sender.balance)
            raise ValueError("Sender does not have enough balance")

    transaction = Transaction(env, amount=amount, receiver=receiver, sender=sender)
    return transaction


def add_transactions(env, wallets, num_transactions, interval, blockchain, end=False):
    """
    Adds transactions to the block.
    """

    tx_count = 0

    while tx_count < (num_transactions * len(wallets)) and not blockchain.stop_process:

        # for every wallet with a balance, makes a random transaction to a random receiver
        # if the wallet has not made num_transactions transactions out

        for i in range(len(wallets)):
            if wallets[i].balance > 0 and len(wallets[i].tx_out) < num_transactions:
                transaction = make_random_transaction(
                    env, blockchain, wallets[i], receivers=wallets
                )
                blockchain.add_transaction(transaction)
                tx_count += 1

            # Checks for negative balance
            if wallets[i].balance < 0:
                print(f"Wallet {i} has {wallets[i].balance} balance")
                raise ValueError("Wallet has negative balance")

            # Checks for duplicate transactions
            if len(wallets[i].tx_out) > num_transactions:
                if len(wallets[i].tx_out) != len(set(wallets[i].tx_out)):
                    print(f"Wallet {i} has duplicate transactions")
                    raise ValueError("Wallet has duplicate transactions and too many")
                raise ValueError("Wallet has too many transactions")

        yield env.timeout(interval)

    if end:
        blockchain.stop_process = True


def begin_mining(
    env,
    miners,
    blockchain,
    blocktime,
    hashrate,
    print_interval,
    num_transactions,
    nodes,
    years,
    difficulty=None,
    blocks=None,
):

    if difficulty is None:
        difficulty = blocktime * (hashrate * len(miners))

    if blocks is None and years is None and num_transactions == 0:
        raise ValueError("Either blocks or years or num_transactions must be provided")

    diff_interval = 2016

    stats = Stats(
        env=env,
        print_interval=print_interval,
        diff_interval=diff_interval,
        blocktime=blocktime,
        hashrate=hashrate,
        years=years,
        miners=miners,
        nodes=nodes,
        blockchain=blockchain,
        blocks=blocks,
        difficulty=difficulty,
    )

    while True:

        winning_miner = mine_block(miners, stats.difficulty)

        yield env.timeout(winning_miner.mine_time)

        # Alert the node
        # This sends the block to the node which is added to the ledger
        # As well this node communicates with its neighbors and updates them.
        winning_miner.win_block(blockchain.get_current_block())

        blockchain.finalize_block(winning_miner)

        stats.add_block_time(blockchain.get_current_block().time_since_last_block)

        # Adjusts difficulty every 2016 blocks
        if len(stats.block_times) % diff_interval == 0:
            stats.update_difficulty()

        if len(blockchain.blocks) == stats.total_blocks:
            blockchain.stop_process = True

        # Prints the blockchain every print_interval blocks and last block

        if len(blockchain.blocks) % print_interval == 0 or (
            blockchain.stop_process and len(blockchain.tx_pool) <= 1
        ):

            # If the blockchain is indicated to be stopped and the pool is empty
            # or the given input blocks(blocks) is reached
            # This will print the stats and break the loop
            if blockchain.stop_process and (
                len(blockchain.tx_pool) <= 1 or stats.total_blocks == blocks
            ):
                print(f"End: {stats.get_stats_str()}")
                break

            else:
                print(stats.get_stats_str())

    print(f"Avg Block Time: {sum(stats.block_times) / len(stats.block_times)}")

    print(
        f"Avg Broadcast Time: {sum(sum(node.broadcast_times) for node in nodes) / len(nodes) / len(blockchain.blocks)}"
    )
    print(f"Total Broadcast Time: {sum(sum(node.broadcast_times) for node in nodes)}")
    print(f"Total Fees: {blockchain.total_fees}")


def main(
    num_miners,
    num_nodes,
    num_neighbors,
    hashrate,
    blocktime,
    blocksize,
    num_wallets,
    num_transactions,
    interval,
    print_interval,
    reward,
    halving,
    years,
    blocks=None,
    difficulty=None,
    latency=0,
    bandwidth=float("inf"),
    fee=0,
):
    if num_neighbors >= num_nodes:
        raise ValueError("Neighbors cannot be greater than or equal to nodes")

    env = simpy.Environment()
    blockchain = BlockChain(env, blocksize, reward, halving, fee)
    nodes = init_nodes(env, num_nodes, num_neighbors, latency, bandwidth)
    wallets = init_wallets(num_wallets)
    miners = init_miners(env, num_miners, hashrate, nodes, wallets)

    env.process(
        add_transactions(
            env,
            wallets,
            num_transactions,
            interval,
            blockchain,
            end=(num_transactions != 0 and blocks is None),
        )
    )

    env.process(
        begin_mining(
            env,
            miners=miners,
            blockchain=blockchain,
            blocktime=blocktime,
            hashrate=hashrate,
            print_interval=print_interval,
            num_transactions=num_transactions,
            nodes=nodes,
            blocks=blocks,
            years=years,
            difficulty=difficulty,
        )
    )

    env.run()


if __name__ == "__main__":
    main(
        num_miners=2,
        num_nodes=2,
        num_neighbors=1,
        num_wallets=10,
        hashrate=10000,
        blocktime=3.27,
        print_interval=100,
        num_transactions=100,
        blocksize=8000,
        interval=5,
        reward=51.8457072,
        halving=9644000,
        years=1,
        latency=0,
        bandwidth=(1024 * 1024),
        fee=0.001,
        difficulty=None,
        blocks=100000,
    )
