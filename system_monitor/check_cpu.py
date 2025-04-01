import psutil
import time
import datetime
import argparse
import os
import sys
import logging
from typing import Optional, Dict, Any, List, Union, Tuple

# --- Constants ---
DEFAULT_MONITOR_DURATION_S: int = 60
DEFAULT_MONITOR_INTERVAL_S: int = 5
DEFAULT_WARN_THRESHOLD_PERCENT: int = 80
INFO_CPU_INTERVAL_S: float = 0.1 # Short interval for quick info checks

# --- Logging Setup ---
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# Prevent adding multiple handlers if the script is imported elsewhere
if not log.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    log.addHandler(handler)

# --- Core Functions ---

def get_cpu_usage(interval: Optional[float] = INFO_CPU_INTERVAL_S, per_cpu: bool = False) -> Union[float, List[float]]:
    """
    Lấy thông tin sử dụng CPU tổng thể hoặc cho từng core.

    Args:
        interval (Optional[float]): Khoảng thời gian để tính toán mức sử dụng (giây).
                                     None hoặc 0.0 trả về so sánh non-blocking với lần gọi trước.
                                     Mặc định là INFO_CPU_INTERVAL_S (0.1s).
        per_cpu (bool): True để trả về danh sách sử dụng cho từng core, False cho tổng thể.

    Returns:
        Union[float, List[float]]: Mức sử dụng CPU (%) - float nếu per_cpu=False, list of floats nếu per_cpu=True.

    Raises:
        psutil.Error: Nếu có lỗi khi truy cập thông tin CPU.
    """
    try:
        return psutil.cpu_percent(interval=interval, percpu=per_cpu)
    except psutil.Error as e:
        log.error(f"Lỗi khi lấy thông tin sử dụng CPU: {e}")
        raise # Re-raise after logging

def get_cpu_info() -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết của CPU (số lõi, tần số).

    Returns:
        Dict[str, Any]: Từ điển chứa thông tin CPU.
                        Trả về None cho các giá trị tần số nếu không lấy được.
    """
    cpu_info: Dict[str, Any] = {
        "physical_cores": None,
        "total_cores": None,
        "max_frequency_mhz": None,
        "current_frequency_mhz": None,
        "min_frequency_mhz": None
    }
    try:
        cpu_info["physical_cores"] = psutil.cpu_count(logical=False)
        cpu_info["total_cores"] = psutil.cpu_count(logical=True)
    except psutil.Error as e:
        log.error(f"Lỗi khi lấy số lượng core CPU: {e}")
    except NotImplementedError:
         log.warning("Không thể xác định số core vật lý trên hệ thống này.")
         cpu_info["total_cores"] = psutil.cpu_count(logical=True) # Try to get logical at least

    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            cpu_info["max_frequency_mhz"] = cpu_freq.max
            cpu_info["current_frequency_mhz"] = cpu_freq.current
            cpu_info["min_frequency_mhz"] = cpu_freq.min
    except psutil.Error as e:
        # Might fail due to permissions or not implemented on the platform/hardware
        log.warning(f"Không thể lấy thông tin tần số CPU: {e}. Có thể cần quyền root/admin.")
    except NotImplementedError:
         log.warning("Thông tin tần số CPU không được hỗ trợ trên hệ thống này.")

    return cpu_info

def get_system_load() -> Optional[Tuple[float, float, float]]:
    """
    Lấy thông tin tải trung bình của hệ thống (1, 5, 15 phút).
    Hoạt động chủ yếu trên Unix/Linux/macOS.

    Returns:
        Optional[Tuple[float, float, float]]: Tuple chứa tải trung bình 1, 5, 15 phút,
                                              hoặc None nếu không hỗ trợ.
    """
    try:
        # getloadavg() returns tuple of floats (load avg over 1, 5, 15 mins)
        return psutil.getloadavg()
    except AttributeError:
        log.info("Thông tin tải trung bình (load average) không có sẵn trên hệ thống này (thường chỉ có trên Unix).")
        return None
    except psutil.Error as e:
        log.error(f"Lỗi khi lấy thông tin tải trung bình: {e}")
        return None
    

def display_cpu_info_and_status(args: argparse.Namespace):
    """Hiển thị thông tin CPU và trạng thái sử dụng hiện tại."""

    print("--- THÔNG TIN CPU ---")
    cpu_info = get_cpu_info()
    print(f"Số lõi vật lý        : {cpu_info.get('physical_cores', 'N/A')}")
    print(f"Tổng số lõi logic    : {cpu_info.get('total_cores', 'N/A')}")

    if cpu_info.get("max_frequency_mhz") is not None:
        print(f"Tần số tối đa        : {cpu_info['max_frequency_mhz']:.2f} MHz")
    if cpu_info.get("min_frequency_mhz") is not None:
        print(f"Tần số tối thiểu     : {cpu_info['min_frequency_mhz']:.2f} MHz")
    if cpu_info.get("current_frequency_mhz") is not None:
        print(f"Tần số hiện tại      : {cpu_info['current_frequency_mhz']:.2f} MHz")    


    print("\n--- TÌNH TRẠNG HỆ THỐNG & CPU ---")