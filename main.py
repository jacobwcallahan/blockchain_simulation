import simpy
from core import Node, Block, Miner, BlockChain, Transaction, Wallet
import random
import math
from init_objs import init_nodes, init_wallets, init_miners


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


def make_random_transaction(env, blockchain, senders, receivers, amount=None):
    """
    Adds transactions to the block.
    """
    receiver = random.choice(receivers)
    sender = random.choice(senders)

    # Ensures the sender has a balance > 0

    while sender == receiver:

        receiver = random.choice(receivers)

    if amount is None:
        amount = random.uniform(0, sender.balance)

        amount = math.floor(amount * 100000) / 100000

        if amount > sender.balance:
            print(amount)
            print(sender.balance)

    transaction = Transaction(env, amount=amount, receiver=receiver, sender=sender)
    blockchain.add_transaction(transaction)


def add_transactions(
    env,
    wallets,
    num_transactions,
    interval,
    blockchain,
):
    """
    Adds transactions to the block.
    """

    transaction_count = 0

    while transaction_count < num_transactions:
        receivers = []
        senders = []

        for wallet in wallets:
            if wallet.balance == 0:
                receivers.append(wallet)
            else:
                receivers.append(wallet)
                senders.append(wallet)

        if len(senders) != 0:
            make_random_transaction(env, blockchain, senders, receivers)
            transaction_count += 1

        yield env.timeout(interval)


def begin_mining(
    env,
    miners,
    blockchain,
    years,
    blocktime,
    hashrate,
    print_interval,
    reward,
    halving,
):

    total_blocks = math.ceil(years * 365 * 24 * 60 * 60 / blocktime)
    print(f"Total Blocks: {total_blocks}")
    reward_amount = reward

    block_times = []

    difficulty = blocktime * (hashrate * len(miners))

    diff_interval = 2016
    halving_count = 0

    for i in range(total_blocks):

        if i % halving == 0 and halving_count < 35:
            reward_amount = reward_amount * (0.5 ** (len(blockchain.blocks) // halving))
            halving_count += 1

        winning_miner = mine_block(miners, difficulty)

        yield env.timeout(winning_miner.mine_time)

        # Alert the node
        # This sends the block to the node which is added to the ledger
        # As well this node communicates with its neighbors and updates them.
        winning_miner.win_block(blockchain.get_current_block())

        block_times.append(blockchain.get_current_block().time_since_last_block)

        blockchain.finalize_block()

        reward_transaction = Transaction(
            env, amount=reward_amount, receiver=winning_miner.wallet
        )

        blockchain.coins += reward_amount

        blockchain.add_transaction(reward_transaction)

        if len(block_times) % diff_interval == 0:
            difficulty = math.ceil(
                difficulty
                * (blocktime / (sum(block_times[-diff_interval:]) / diff_interval))
            )

        if (i + 1) % print_interval == 0:
            block_num = f"{i + 1}/{total_blocks}"
            block_percent = f"{(round((i + 1)/total_blocks*100, 2))}%"
            abt = (
                round(sum(block_times[-print_interval:]) / print_interval, 2)
                if len(block_times) >= print_interval
                else 0
            )
            coins = blockchain.coins

            print(
                f"B: {block_num} {block_percent} | ABT: {abt} | Tx: {blockchain.total_transactions} Diff: {difficulty} | C: {coins // 1000}K"
            )

    print(f"Avg Block Time: {sum(block_times) / total_blocks}")


def main(
    num_miners=2,
    hashrate=10000,
    num_nodes=2,
    num_neighbors=1,
    blocktime=1000,
    blocksize=100,
    num_wallets=10,
    num_transactions=10,
    interval=10,
    print_interval=10,
    reward=100,
    halving=100,
    years=1,
):
    if num_neighbors >= num_nodes:
        raise ValueError("Neighbors cannot be greater than or equal to nodes")

    env = simpy.Environment()

    blockchain = BlockChain(env)
    nodes = init_nodes(env, num_nodes, num_neighbors, blockchain)
    wallets = init_wallets(num_wallets)
    miners = init_miners(
        env, num_miners, hashrate, nodes, wallets, random_hashrate=False
    )

    env.process(add_transactions(env, wallets, num_transactions, interval, blockchain))

    env.process(
        begin_mining(
            env,
            miners,
            blockchain,
            years,
            blocktime,
            hashrate,
            print_interval,
            reward,
            halving,
        )
    )

    env.run()

    # Transaction(env, amount=0.5, receiver=wallets[0], sender=miners[0].wallet)


if __name__ == "__main__":
    main(
        num_miners=4,
        num_nodes=5,
        num_neighbors=2,
        num_wallets=100,
        hashrate=10000,
        blocktime=100,
        print_interval=1000,
        num_transactions=0,
        halving=1000,
        years=10,
    )
