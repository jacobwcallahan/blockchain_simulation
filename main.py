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


def make_random_transaction(
    env, sender, receivers, miners, interval, num_transactions, amount=None
):
    """
    Creates a transaction between a sender and a receiver.
    This is based on the receiver with the least balance strictly for the purpose of the simulation.

    If the sender has a minimum balance, the transaction will be made to a random receiver.

    Args:
        env (simpy.Environment): The environment.
        blockchain (BlockChain): The blockchain.
        sender (Wallet): The sender of the transaction.
        receivers (list): The receivers of the transaction.
        amount (float): The amount of the transaction.
    """

    receiver = min(receivers, key=lambda x: x.balance)

    # Ensures the sender has a balance > 0

    while sender == receiver:

        receiver = min(receivers, key=lambda x: x.balance)
        if receiver == sender:
            receiver = random.choice(receivers)

    if amount is None:

        if sender in miners:
            #! This is a hack to ensure that miners have a balance > 0
            # This is only for the purpose of the simulation and should be removed

            # It was found many wallets had a balance near 0 as the miners transactions went through quicker than they could be added to the blockchain
            # This lead to a weak economy as the miners could not spend their own coins and the other wallets had no coins (or nearly no coins)
            amount = sender.balance

        else:
            # This is a hack to ensure that the transaction is not too large
            # Allows for many transactions to be made without the wallets having to be near 0
            amount = random.uniform(sender.balance * 0.05, sender.balance * 0.1)

        if amount <= 0:
            print(sender.balance)
            raise ValueError("Amount is less than 0. This should not happen.")

        if amount > sender.balance:
            print(amount)
            print(sender.balance)
            raise ValueError("Sender does not have enough balance")

    transaction = Transaction(env, amount=amount, receiver=receiver, sender=sender)
    return transaction


def add_transactions(
    env,
    wallets,
    num_transactions,
    interval,
    blockchain,
    miners,
    end=False,
):
    """
    Adds transactions to the block.
    """

    tx_count = 0

    while tx_count < (num_transactions * len(wallets)) and not blockchain.stop_process:

        # for every wallet with a balance, makes a random transaction to a random receiver
        # if the wallet has not made num_transactions transactions out

        for i in range(len(wallets)):

            # Checks if the wallet has a balance and has not made num_transactions transactions out
            # Rounds the balance to 15 decimal places to avoid floating point errors

            if (
                round(wallets[i].balance, 15) > 0
                and wallets[i].tx_out < num_transactions
            ):
                transaction = make_random_transaction(
                    env,
                    wallets[i],
                    receivers=wallets,
                    miners=miners,
                    interval=interval,
                    num_transactions=num_transactions,
                )

                blockchain.add_transaction(transaction)
                tx_count += 1

            # Checks for negative balance
            if wallets[i].balance < 0:
                print(f"Wallet {i} has {wallets[i].balance} balance")
                raise ValueError("Wallet has negative balance")

            # Checks for duplicate transactions
            if wallets[i].tx_out > num_transactions:
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
    diff_interval=2016,
    difficulty=None,
    blocks=None,
):
    """This is the main mining process. It begins mining blocks  in a loop and updates the blockchain.

    Args:
        env (simpy.Environment): The environment.
        miners (list): The miners.
        blockchain (BlockChain): The blockchain.
        blocktime (float): The blocktime.
        hashrate (bool): The hashrate.
        print_interval (int): The print interval.
        num_transactions (int): The number of transactions.
        nodes (list): The nodes.
        years (int): The number of years.
        diff_interval (int, optional): The difficulty interval. Defaults to 2016.
        difficulty (int, optional): The difficulty. Defaults to None.
        blocks (int, optional): The number of blocks. Defaults to None.

    Raises:
        ValueError: If the difficulty is not provided and the blocktime, hashrate, and number of miners are not provided.
        ValueError: If the blocks, years, or num_transactions are not provided.

    """

    if difficulty is None:
        difficulty = blocktime * (hashrate * len(miners))

    if blocks is None and years is None and num_transactions == 0:
        raise ValueError("Either blocks or years or num_transactions must be provided")

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

    # Main mining Loop
    while True:

        winning_miner = mine_block(miners, stats.difficulty)

        yield env.timeout(winning_miner.mine_time)

        blockchain.finalize_block()

        # Alert the node
        # This sends the block to the node which is added to the ledger
        # As well this node communicates with its neighbors and updates them.
        yield env.process(winning_miner.win_block(blockchain.get_current_block()))

        stats.add_block_time(blockchain.get_current_block().time_since_last_block)

        blockchain.create_block(env, winning_miner)

        # This adds the total time from the latency and bandwidth of the nodes
        stats.add_total_time(
            sum(node.broadcast_times[-1] for node in nodes)
            + blockchain.get_current_block().time_since_last_block
        )

        # Adjusts difficulty every 2016 blocks
        if len(stats.block_times) % diff_interval == 0:
            stats.update_difficulty()

        if blockchain.total_blocks == stats.total_blocks:
            blockchain.stop_process = True

        # Prints the blockchain every print_interval blocks and last block

        if blockchain.total_blocks % print_interval == 0 or (
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

    if nodes[0].latency > 0 or nodes[0].bandwidth < float("inf"):
        print(
            f"Avg Broadcast Time per block: {sum(sum(node.broadcast_times) for node in nodes) / len(nodes) / blockchain.total_blocks}"
        )
        print(
            f"Total Broadcast Time: {sum(sum(node.broadcast_times) for node in nodes)}"
        )

    if blockchain.fee > 0:
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

    if fee > 1:
        raise ValueError(
            "Fee must be between 0 and 1. Fee is a percentage of the transaction amount."
        )

    if fee < 0:
        raise ValueError("Fee must be greater than 0")

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
            miners=miners,
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
        num_miners=5,
        num_nodes=2,
        num_neighbors=1,
        num_wallets=10,
        hashrate=10000,
        blocktime=3.27,
        print_interval=1000000,
        num_transactions=0,
        blocksize=32000,
        interval=10.0,
        reward=51.8457072,
        halving=964400,
        years=10,
        blocks=None,
        difficulty=None,
        latency=0,
        bandwidth=float("inf"),
        fee=0,
    )
