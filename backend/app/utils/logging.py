import logging
import sys


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def log_print(message: str):
    """Print with immediate flush and logging"""
    print(message, flush=True)
    logging.getLogger(__name__).info(message)
