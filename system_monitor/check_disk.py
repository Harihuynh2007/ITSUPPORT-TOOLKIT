import psutil
import os
import time
import datetime
import argparse
import sys
import logging
from tabulate import tabulate


DEFAULT_THRESHOLD_PERCENT = 80
DEFAULT_MONITOR_INTERVAL_SEC = 5
DEFAULT_MONITOR_DURATION_SEC = 60
DEFAULT_LARGE_FILES_COUNT = 10
DEFAULT_LARGE_FILES_MIN_SIZE_MB = 10
BYTES_PER_MB = 1024 * 1024

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)