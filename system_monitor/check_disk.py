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

    if ignore_fstypes is None:
        ignore_fstypes = ['tmpfs', 'devtmpfs', 'squashfs', 'iso9660', 'udf']

    for partition in partition:
        if partition.fstype.lower() in ignore_fstypes:
            logger.debug(f"Bỏ qua phân vùng {partition.device} (mountpoint: {partition.mountpoint}) do fstype: {partition.fstype}")
            continue

        if include_devices:
            included = False
            for pattern in include_devices:
                if partition.device.startswith(pattern):
                    included = True
                    break
                if not included:
                    logger.debug(f"Bỏ qua phân vùng {partition.device} do khong khop include_devices:{include_devices}")
                    continue
        try:
            usage = psutil.disk_usage(partition.moutpoint)    
            disk_info.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            })    
        except PermissionError:
            logger.warning(f"Không có quyền truy cập thông tin usage cho {partition.mountpoint}. Bỏ qua.")
        except FileNotFoundError:
             logger.warning(f"Mountpoint {partition.mountpoint} không tồn tại (có thể đã unmount?). Bỏ qua.")
        except Exception as e:
            logger.error(f"Lỗi không xác định khi lấy usage cho {partition.mountpoint}: {e}. Bỏ qua.")
    return disk_info

def get_io_stats():
    """
    Lấy thông tin I/O ổ cứng.
    """
    try :
        io_stats = psutil.disk_io_counters(perdisk = True)
        return io_stats
    except NotImplementedError:
        logger.warning("Lấy thông tin I/O chi tiết từng disk không được hỗ trợ trên hệ thống này.")
        return None
    except Exception as e:
        logger.error(f"Lỗi khi lấy thông tin I/O: {e}")
        return None

def monitor_disk(duration=DEFAULT_MONITOR_DURATION_SEC,
                 interval=DEFAULT_MONITOR_INTERVAL_SEC,
                 threshold=DEFAULT_THRESHOLD_PERCENT,
                 mountpoint=None,
                 ignore_fstypes=None,
                 include_devices=None):
    """
    Giám sát ổ cứng trong khoảng thời gian xác định, hiển thị cả I/O rate.

    Args:
        duration (int): Thời gian giám sát (giây).
        interval (int): Khoảng thời gian giữa các lần kiểm tra (giây).
        threshold (int): Ngưỡng cảnh báo sử dụng ổ cứng (%).
        mountpoint (str): Đường dẫn phân vùng cụ thể cần giám sát (nếu None thì giám sát tất cả đã lọc).
        ignore_fstypes (list): Danh sách fstypes cần bỏ qua.
        include_devices (list): Danh sách pattern device cần bao gồm.
    """

    start_time = time.time()
    end_time = start_time + duration

    if mountpoint:
        logger.info(f"Bắt đầu giám sát ổ cứng tại '{mountpoint}' trong {duration}s (interval: {interval}s, ngưỡng: {threshold}%)")
    else:
        logger.info(f"Bắt đầu giám sát tất cả ổ cứng hợp lệ trong {duration}s (interval: {interval}s, ngưỡng: {threshold}%)")


    # Lưu trữ trạng thái I/O trước đó để tính rate
    last_io_stats = get_io_stats()
    last_check_time = start_time
    alerts = 0

    try:
        while time.time() < end_time:
            current_time = time.time()
            time_data = current_time - last_check_time
            if time_data <= 0:# Tránh chia cho 0 nếu interval quá nhỏ hoặc lỗi time
                time_data = 1

        disk_info = get_disk_info(ignore_fstypes, include_devices)
        logger.info(f"--- Kiểm tra lúc: {datetime.datetime.now():%Y-%m-%d %H:%M:%S} ---")

        if mountpoint :
            found = False
            for disk in disk_info:
                if disk["mountpoint"] == mountpoint:
                    found = True
                    status = "Bình thường"
                    if disk["percent"] >= threshold:
                        status = f"CẢNH BÁO (>={threshold}%)"