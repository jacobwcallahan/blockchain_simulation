CS595 Project 2 – Blockchain Simulation
Jacob Callahan
Summer 2025

====================================
PROJECT OVERVIEW
====================================
This project implements a discrete-event blockchain simulation using SimPy. It models key features of blockchain systems including:

- Mining and difficulty retargeting
- Wallet-based transaction generation
- Block propagation across a P2P network
- Coin issuance, halving schedules, and inflation tracking
- CLI-driven configuration for modular experimentation

====================================
REQUIREMENTS
====================================
Python 3.8+  
Install dependencies with:
pip install simpy

====================================
FILE STRUCTURE
====================================

sim-blockchain.py - Entry-point script using argparse to parse CLI flags  
main.py - Main simulation logic for the two main processes, mining process and transaction process
init_objs.py - Fucntions for initializing nodes, miners, and wallets  
stats.py - Tracking and printing of blockchain statistics over time  
core - Includes the BlockChain, Node, Wallet, Block, Miner classes 

====================================
USAGE
====================================

Key options:

- `--miners` : Number of miners in the simulation
- `--nodes` : Number of nodes in the network
- `--neighbors` : Max neighbors per node (for propagation)
- `--wallets` : Number of wallet agents
- `--transactions` : Transactions per wallet (This will stop the process when these are complete if given)
- `--interval` : Time between wallet transactions (seconds)
- `--blocktime` : Target block time (seconds)
- `--blocksize` : Max transactions per block
- `--reward` : Block reward in coins
- `--halving` : Blocks per reward halving
- `--years` : Run simulation for this many years
- `--blocks` : OR stop after this many blocks (This stops the simulation at given amount of blocks, regardlenss of 'transactions')
- `--difficulty` : Starting difficulty (optional)
- `--latency` : Simulated network latency
- `--bandwidth` : Simulated network bandwidth
- `--print` : Block print summary interval
- `--fee` : % transaction fee (0.0 to 1.0)
- `--debug` : If set, prints summary every block

====================================
EXAMPLE COMMANDS
====================================

Run a basic 1-year simulation without transaction activity and no blocks set

To run the simulation:

python3 sim-blockchain.py --miners 5 --hashrate 10000 --nodes 2 --neighbors 1 --blocktime 3.27 --blocksize 32000 --wallets 10 --transactions 0 --interval 10.0 --print 1000000 --reward 51.8457072 --halving 964400 --years 1 --bandwidth 1024 --latency .1 --fee .01


====================================
TROUBLESHOOTING
====================================

- Make sure neighbor count is less than number of nodes.
- Floating-point rounding may cause slight inconsistencies. Transaction logic defends against this but it may still appear
- For large workloads (e.g., 1000 wallets with 1000 tx), simulation may take minutes.

====================================
AUTHOR
====================================
Jacob Callahan  
CS595 – Summer 2025
