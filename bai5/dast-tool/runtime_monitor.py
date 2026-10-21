import psutil


class RuntimeMonitor:
    def __init__(self, pid: int):
        self.pid = pid
        self.process = psutil.Process(pid)

    def get_cpu_usage(self) -> float:
        return self.process.cpu_percent(interval=0.1)

    def get_memory_usage(self) -> int:
        return self.process.memory_info().rss

    def get_open_files(self) -> list:
        return self.process.open_files()
