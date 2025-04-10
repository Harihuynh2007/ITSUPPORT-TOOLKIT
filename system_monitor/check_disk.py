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

file_handle = None

def get_size(bytes_val, suffix = "B"):
    """
    Chuyển đổi đơn vị bytes sang nhân hệ số (KB, MB, GB, TB,...)
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if abs(bytes_val) < factor:
            return f"{bytes_val:3.2f} {unit}{suffix}"
        bytes_val /= factor
    return f"{bytes_val:.2f}E{suffix}"

def setup_file_logging(log_file):
    """Cấu hình logging vào file."""
    global file_handle
    try:
        log_dir  = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        file_handler = logging.FileHandler(log_file, mode= "a")    
        file_handler .setFormatter(log_formatter)
        logger.addHandler(file_handler)
        logger.info(f"--- Bat dau phien lam viec moi---")
    except OSError as e:
        logger.error(f"Khong the tao hoac mo file log '{log_file}': {e}")    



def get_disk_info(ignore_fstypes = None, include_devices= None):
    """
    Lấy thông tin chi tiết các phân vùng ổ cứng, có lọc theo fstype và device.

    Args:
        ignore_fstypes (list, optional): Danh sách các loại fstype cần bỏ qua.
        include_devices (list, optional): Danh sách các pattern tên device cần bao gồm (ví dụ: ['/dev/sd', '/dev/nvme']).

    Returns:
        list: Danh sách thông tin các phân vùng đã lọc.
    """

    partitions = psutil.disk_partitions(all = False)
    disk_info = []

    
