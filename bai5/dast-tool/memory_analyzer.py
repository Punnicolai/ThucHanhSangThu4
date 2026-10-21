import gc


class MemoryAnalyzer:
    """Perform basic Python garbage-collection and integer-bound checks."""

    def check_memory_leaks(self) -> list[object]:
        gc.collect()
        return list(gc.garbage)

    def check_overflow(self, value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and (
            value > 2**63 - 1 or value < -(2**63)
        )
