import logging
import sys
from datetime import datetime

def setup_logger():
    logger = logging.getLogger('DeskFeedAgent')

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(f'agent_{datetime.now().strftime("%Y%m%d")}.log')
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
