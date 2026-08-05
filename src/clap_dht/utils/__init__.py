import timeit
import logging

logger = logging.getLogger("UTILS")

class Timer:
    def __init__(self, label = "", info = False):
        self.label = label
        self.logger_func = logger.info if info else logger.debug

    def __enter__(self):
        self.logger_func(f"{self.label} start")
        self.start = timeit.default_timer()
        
    def __exit__(self, exc_type, exc, tb):
        self.end = timeit.default_timer()
        self.logger_func(f"{self.label} end {self.end - self.start:.4f}s")