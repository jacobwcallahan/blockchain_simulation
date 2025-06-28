import math


class Stats:
    """
    Class to track and print statistics for the blockchain. It stores certain variables as well that help run the simulation/blockchain.
    """

    def __init__(
        self,
        env,
        print_interval,
        diff_interval,
        blocktime,
        hashrate,
        years,
        miners,
        nodes,
        blockchain,
        difficulty,
        blocks=None,
    ):

        self.print_interval = print_interval
        self.diff_interval = diff_interval

        self.block_times = []
        self.total_times = []
        self.difficulty = difficulty

        self.nodes = nodes
        self.diff_interval = diff_interval
        self.blockchain = blockchain
        self.blocktime = blocktime

        if blocks is None:
            self.total_blocks = math.ceil((years * 365 * 24 * 60 * 60) / blocktime)
        else:
            self.total_blocks = blocks

        self.env = env
        self.last_print_time = 0
        self.old_fees = 0

        self.print_dict = {
            "block_num": 0,
            "block_percent": 0,
            "abt": 0,
            "tps": 0,
            "tx_num": 0,
            "difficulty": 0,
            "coins": 0,
            "inflation": 0,
            "eta": 0,
            "hashrate": hashrate,
            "pool": 0,
            "io_requests": 0,
            "nmb": 0,
            "fees": 0,
            "network_time": 0,
        }

    def get_stats_str(self):

        self.update_print_dict()

        print_list = [
            f"B:{self.print_dict['block_num']}/{self.total_blocks}",
            f"{round(self.print_dict['block_percent'], 2)}%",
            f"ABT:{round(self.print_dict['abt'], 2)}s",
            f"Diff:{round(self.print_dict['difficulty'] / 1000000, 3)}M",
            f"H:{self.print_dict['hashrate']}",
            f"Infl:{round(self.print_dict['inflation'], 2)}%",
            f"ETA:{int(round(self.print_dict['eta'], 2))}s",
            f"Tx:{round(self.blockchain.total_transactions, 2)}",
            f"TPS:{round(self.print_dict['tps'], 2)}",
            f"C:{round(self.print_dict['coins'] / 1000, 2)}K",
            f"NMB:{round(self.print_dict['nmb'], 2)}",
            f"Pool:{self.print_dict['pool']}",
            f"IO:{self.print_dict['io_requests']}",
        ]

        if self.print_dict["network_time"] > 0:
            print_list.append(
                f"Network Time:{round(self.print_dict['network_time'], 2)}s"
            )

        if self.print_dict["fees"] > 0 or self.old_fees > 0:
            print_list.append(f"AFB:{round(self.print_dict['fees'], 2)}")

        return " ".join(print_list)

    def add_block_time(self, block_time):
        self.block_times.append(block_time)

    def add_total_time(self, total_time):
        self.total_times.append(total_time)

    def update_difficulty(self):

        self.difficulty = math.ceil(
            self.difficulty
            * (
                self.blocktime
                / (sum(self.total_times[-self.diff_interval :]) / self.diff_interval)
            )
        )

    def update_print_dict(self):
        """
        Updates the print dictionary with the current statistics.
        This is called every print interval.

        The order of this matters (relatively)as some old values (e.g. block_num) are used in other calculations.
        """
        time_since_last_print = self.env.now - self.last_print_time

        self.set_abt()

        self.set_tps(time_since_last_print)

        self.set_tx_num()

        self.set_inflation(time_since_last_print)

        self.set_eta()

        self.set_fees()

        self.set_network_time()

        self.set_block_num()

        self.set_eta()

        self.set_coins()

        self.set_difficulty()

        self.set_pool()

        self.set_block_percent()

        self.set_nmb()

        self.set_io_requests()

        self.last_print_time = self.env.now

    def set_abt(self):
        self.print_dict["abt"] = (
            sum(self.total_times[-self.print_interval :]) / self.print_interval
        )

    def set_tps(self, time_since_last_print):
        # tx amt since from last print / time since last print
        self.print_dict["tps"] = (
            self.blockchain.total_transactions - self.print_dict["tx_num"]
        ) / time_since_last_print

    def set_tx_num(self):
        self.print_dict["tx_num"] = self.blockchain.total_transactions

    def set_inflation(self, time_since_last_print):
        # (Total coins / last coins) / time = inflation per second
        # Times the number of seconds in a year -> Expected inflation per year

        if time_since_last_print == 0 or self.print_dict["coins"] == 0:
            self.print_dict["inflation"] = 0
        else:
            self.print_dict["inflation"] = (
                (
                    (self.blockchain.coins / self.print_dict["coins"])
                    / time_since_last_print
                )
                * 60
                * 60
                * 24
                * 365
            )

    def set_block_num(self):
        self.print_dict["block_num"] = self.blockchain.total_blocks

    def set_block_percent(self):
        self.print_dict["block_percent"] = (
            self.print_dict["block_num"] / self.total_blocks * 100
        )

    def set_difficulty(self):
        self.print_dict["difficulty"] = self.difficulty

    def set_pool(self):
        self.print_dict["pool"] = len(self.blockchain.tx_pool)

    def set_eta(self):
        # time to complete remaining blocks based on average block time
        self.print_dict["eta"] = self.print_dict["abt"] * (
            self.total_blocks - self.print_dict["block_num"]
        )

    def set_coins(self):
        self.print_dict["coins"] = self.blockchain.coins

    def set_io_requests(self):
        self.print_dict["io_requests"] = sum(
            node.total_io_requests for node in self.nodes
        )

    def set_nmb(self):
        self.print_dict["nmb"] = sum(node.network_usage for node in self.nodes) / (
            1024 * 1024
        )

    def set_fees(self):
        new_fees = self.blockchain.total_fees - self.old_fees
        self.old_fees = self.blockchain.total_fees
        self.print_dict["fees"] = new_fees / (
            self.blockchain.total_blocks - self.print_dict["block_num"]
        )

    def set_network_time(self):
        # This is the sum of each node's broadcast times for the last print interval blocks
        self.print_dict["network_time"] = sum(
            sum(node.broadcast_times[-self.print_interval :]) for node in self.nodes
        )
