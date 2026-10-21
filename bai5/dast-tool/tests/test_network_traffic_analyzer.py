import unittest
from unittest.mock import patch

from network_traffic_analyzer import NetworkTrafficAnalyzer


class TestNetworkTrafficAnalyzer(unittest.TestCase):
    def test_returns_per_interface_statistics(self):
        fake_counters = type(
            "Counters",
            (),
            {"_asdict": lambda self: {"bytes_sent": 12}},
        )()
        with patch(
            "network_traffic_analyzer.psutil.net_io_counters",
            return_value={"eth0": fake_counters},
        ):
            result = NetworkTrafficAnalyzer().get_network_stats()
        self.assertEqual(result, {"eth0": {"bytes_sent": 12}})


if __name__ == "__main__":
    unittest.main()
