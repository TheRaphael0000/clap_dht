import timeit
import logging

logger = logging.getLogger()

class Timer:
    def __init__(self, label = ""):
        self.label = label

    def __enter__(self):
        logger.debug(f"{self.label} start")
        self.start = timeit.default_timer()
        
    def __exit__(self, exc_type, exc, tb):
        self.end = timeit.default_timer()
        logger.debug(f"{self.label} end {self.end - self.start:.4f}s")