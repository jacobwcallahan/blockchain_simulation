import argparse
from main import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--miners", type=int, default=5)
    parser.add_argument("--nodes", type=int, default=2)
    parser.add_argument("--neighbors", type=int, default=1)
    parser.add_argument("--wallets", type=int, default=10)
    parser.add_argument("--hashrate", type=int, default=10000)
    parser.add_argument("--blocktime", type=float, default=100)
    parser.add_argument("--print", type=int, default=144)
    parser.add_argument("--transactions", type=int, default=0)
    parser.add_argument("--blocksize", type=int, default=100)
    parser.add_argument("--interval", type=float, default=10)
    parser.add_argument("--reward", type=float, default=50)
    parser.add_argument("--halving", type=int, default=210000)
    parser.add_argument("--years", type=int, default=1)
    parser.add_argument("--latency", type=float, default=0)
    parser.add_argument("--bandwidth", type=int, default=float("inf"))
    parser.add_argument("--fee", type=float, default=0)
    parser.add_argument("--difficulty", type=float, default=None)
    parser.add_argument("--blocks", type=int, default=None)
    parser.add_argument(
        "--debug", action="store_true", help="Print summary every block if set."
    )

    args = parser.parse_args()

    if args.debug:
        print_interval = 1

    print(
        f"Miners: {args.miners} | Nodes: {args.nodes} | Neighbors: {args.neighbors} | Wallets: {args.wallets} | Hashrate: {args.hashrate} | Blocktime: {args.blocktime} | Print: {args.print} | Transactions: {args.transactions} | Blocksize: {args.blocksize} | Interval: {args.interval} | Reward: {args.reward} | Halving: {args.halving} | Years: {args.years} | Blocks: {args.blocks} | Difficulty: {args.difficulty} | Latency: {args.latency} | Bandwidth: {args.bandwidth} | Fee: {args.fee}"
    )

    main(
        num_miners=args.miners,
        num_nodes=args.nodes,
        num_neighbors=args.neighbors,
        num_wallets=args.wallets,
        hashrate=args.hashrate,
        blocktime=args.blocktime,
        print_interval=args.print,
        num_transactions=args.transactions,
        blocksize=args.blocksize,
        interval=args.interval,
        reward=args.reward,
        halving=args.halving,
        years=args.years,
        latency=args.latency,
        bandwidth=args.bandwidth,
        fee=args.fee,
        difficulty=args.difficulty,
        blocks=args.blocks,
    )
