import os
import unittest

from runtime_monitor import RuntimeMonitor


class TestRuntimeMonitor(unittest.TestCase):
    def test_reads_current_process_metrics(self):
        monitor = RuntimeMonitor(os.getpid())
        self.assertIsInstance(monitor.get_cpu_usage(), float)
        self.assertGreater(monitor.get_memory_usage(), 0)
        self.assertIsInstance(monitor.get_open_files(), list)


if __name__ == "__main__":
    unittest.main()
