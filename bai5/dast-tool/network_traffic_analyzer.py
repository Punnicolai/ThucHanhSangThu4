import psutil


class NetworkTrafficAnalyzer:
    def get_network_stats(self) -> dict:
        counters = psutil.net_io_counters(pernic=True)
        if counters is None:
            return {}
        return {
            interface: stats._asdict()
            for interface, stats in sorted(counters.items())
        }
