import os
from pathlib import Path

from memory_analyzer import MemoryAnalyzer
from network_traffic_analyzer import NetworkTrafficAnalyzer
from runtime_monitor import RuntimeMonitor
from security_behavior_checker import SecurityBehaviorChecker
from virtual_sandbox import VirtualSandbox


def main() -> None:
    pid = os.getpid()
    print(f"[+] Monitoring current process: {pid}")

    monitor = RuntimeMonitor(pid)
    print("CPU Usage:", monitor.get_cpu_usage())
    print("Memory Usage:", monitor.get_memory_usage())
    print("Open Files:", monitor.get_open_files())

    memory_analyzer = MemoryAnalyzer()
    print("Memory Leaks:", memory_analyzer.check_memory_leaks())
    print("Overflow Test:", memory_analyzer.check_overflow(2**64))
    print("Network Stats:", NetworkTrafficAnalyzer().get_network_stats())

    app_source = Path(__file__).with_name("app.py")
    suspicious_calls = SecurityBehaviorChecker(app_source).suspicious_calls()
    print("Suspicious Calls:", suspicious_calls)
    with VirtualSandbox() as sandbox:
        stdout, stderr = sandbox.run_isolated("echo Hello Sandbox")
    print("Sandbox stdout:", stdout, end="")
    print("Sandbox stderr:", stderr, end="")


if __name__ == "__main__":
    main()
