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

file_handler = None

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
                        alerts += 1
                        logger.warning(f"Mountpoint '{disk['mountpoint']}' ({disk['device']}) đạt {disk['percent']:.1f}% sử dụng.")
                    else:
                        logger.info(f"Mountpoint '{disk['mountpoint']}' ({disk['device']}): {disk['percent']:.1f}% - Used: {get_size(disk['used'])} / Total: {get_size(disk['total'])}")    
                    break
                if not found:
                    logger.warning(f"Không tìm thấy thông tin cho mountpoint '{mountpoint}'. Có thể nó đã bị lọc hoặc không tồn tại.")
        else:
            usage_data = []
            for disk in disk_info:
                status = "ok"
                log_level = logging.INFO
                if disk['percent'] >= threshold:
                    status = f"WARN (>={threshold}%)"
                    alerts += 1
                    log_level = logging.WARNING

                usage_data.apped([
                    disk["device"],
                        disk["mountpoint"],
                        f"{disk['percent']:.1f}%",
                        get_size(disk['used']),
                        get_size(disk['total']),
                        status
                ])    
            if usage_data:
                print("\n=== Tình trạng sử dụng ===")
                print(tabulate(usage_data, headers=["Thiết bị", "Mountpoint", "% Used", "Đã dùng", "Tổng", "Trạng thái"], tablefmt="pretty"))
            else:
                logger.info("Không có phân vùng nào để hiển thị sau khi lọc.")   


        current_io_stats = get_io_stats()
        if current_io_stats and last_io_stats:
            io_rate_data = []
            for disk_name, current_stats in current_io_stats.items():
                last_stats = last_io_stats[disk_name]
                if last_stats:
                    time_delta = (current_stats.timestamp - last_stats.timestamp).total_seconds()
                    
                    read_rate = (current_stats.read_bytes - last_stats.read_bytes) / time_delta
                    write_rate = (current_stats.write_bytes - last_stats.write_bytes) / time_delta
                    read_iops = (current_stats.read_count - last_stats.read_count) / time_delta
                    write_iops = (current_stats.write_count - last_stats.write_count) / time_delta

                    
                    # Chỉ hiển thị nếu có hoạt động I/O đáng kể
                    if read_rate > 1 or write_rate > 1 or read_iops > 0.1 or write_iops > 0.1:
                            io_rate_data.append([
                            disk_name,
                            f"{get_size(read_rate)}/s",
                            f"{read_iops:.1f}/s",
                            f"{get_size(write_rate)}/s",
                            f"{write_iops:.1f}/s"
                        ])

                if io_rate_data:
                    print("\n=== Tốc độ I/O (hiện tại) ===")
                    print(tabulate(io_rate_data, headers=["Thiết bị", "Đọc", "Read IOPS", "Ghi", "Write IOPS"], tablefmt="pretty", floatfmt=".1f"))            


            # Cập nhật trạng thái cho lần lặp sau
            last_io_stats = current_io_stats
            last_check_time = current_time

            # Ngủ đến lần kiểm tra tiếp theo (trừ đi thời gian đã dùng để kiểm tra)
            remaining_time = end_time - time.time()
            sleep_time = max(0, min(interval - (time.time() - current_time), remaining_time))
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt :
        logger.info("\nGiám sát bị dừng bởi người dùng.")    
    finally:
        summary = f"\nKết thúc giám sát ổ cứng. Tổng số cảnh báo dung lượng: {alerts}"
        logger.info(summary)
        if file_handler:
            logger.removeHandler(file_handler)  
            file_handler.close()

def find_large_files(path='.', top_n=DEFAULT_LARGE_FILES_COUNT, min_size_bytes=DEFAULT_LARGE_FILES_MIN_SIZE_MB * BYTES_PER_MB):
    """
        Tìm các file lớn trong đường dẫn chỉ định.

        Args:
            path (str): Đường dẫn cần tìm kiếm.
            top_n (int): Số lượng file lớn nhất cần hiển thị.e
            min_size_bytes (int): Kích thước tối thiểu (bytes).

        Returns:
            list: Danh sách các tuple (filepath, size) của các file lớn nhất.
        """
    large_files = []
    logger.info(f"Bắt đầu tìm kiếm file lớn hơn {get_size(min_size_bytes)} trong '{path}'...")


    for dirpath, dirnames, filenames in os.walk(path, topdown = True):
        accessible_dirs = []
        for d in list(dirnames):
            dir_full_path = os.path.join(dirpath, d)
            if not os.access(dir_full_path, os.R_OK | os.X_OK):
                logger.warning(f"Không có quyền truy cập thư mục: {dir_full_path}. Bỏ qua.")
                dirnames.remove(d)
            else:
                accessible_dirs.append(d)

        for filename in filenames:
            filepath = os.path.join(dirpath,filename)
            try:
                if not os.path.islink(filepath) and os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    if size >= min_size_bytes:
                        large_files.append((filepath, size)) 
                        # Tối ưu: Nếu đã có nhiều hơn N file, so sánh và giữ lại top N
                        if len(large_files) > top_n:
                            large_files.sort(key=lambda x: x[1], reverse=True)
                            large_files = large_files[:top_n]
            except FileNotFoundError:
                logger.debug(f"File {filepath} không tìm thấy (có thể đã bị xóa giữa chừng).")
                continue # File có thể đã bị xóa giữa lúc liệt kê và getsize
            except OSError as e:
                logger.warning(f"Không thể lấy kích thước file '{filepath}': {e}. Bỏ qua.")
                continue

    large_files.sort(key = lambda x:x[1], reverse = True)
    logger.info(f"Tìm kiếm hoàn tất. Tìm thấy {len(large_files)} file thỏa mãn.")
    return large_files[:top_n]

def display_disk_info(disk_info_list, show_io = False):
    """Hiển thị thông tin ổ cứng và I/O dưới dạng bảng."""
    if not disk_info_list:
        logger.info("Không có thông tin ổ cứng nào để hiển thị (có thể đã bị lọc hết).")
        return

    print("\n=== THÔNG TIN SỬ DỤNG Ổ CỨNG ===")
    disk_data = []
    warnings = []
    for disk in disk_info_list:
        disk_data.append({
            disk["device"],
            disk["mountpoint"],
            disk["fstype"],
            get_size(disk["total"]),
            get_size(disk["used"]),
            get_size(disk["free"]),
            f"{disk['percent']:.1f}%"
        })        
        if disk["percent"] >= DEFAULT_THRESHOLD_PERCENT:
            warnings.append(f"CẢNH BÁO: Ổ đĩa {disk['device']} ({disk['mountpoint']}) đang sử dụng {disk['percent']:.1f}% dung lượng!")

    print(tabulate(disk_data,
                    headers=["Thiết bị", "Mountpoint", "Hệ thống file", "Tổng", "Đã dùng", "Còn trống", "% Used"],
                    tablefmt="pretty")) # "grid" hoặc "pretty"

    if warnings:
        print("\n--- Cảnh báo dung lượng ---")
        for warn in warnings:
            print(warn)

    if show_io:
        io_stats = get_io_stats()

        if io_stats:
            print("\n=== THÔNG TIN I/O ===")
            io_data= []
            for disk_name, stats in io_stats.items():
                is_relevant = any(disk_name in d['device'] for d in disk_info_list) if disk_info_list else True
                if is_relevant: # Chỉ hiển thị I/O cho các disk có thể liên quan
                    io_data.append([
                        disk_name,
                        get_size(stats.read_bytes),
                        f"{stats.read_count:,}", # Định dạng số lớn
                            get_size(stats.write_bytes),
                            f"{stats.write_count:,}"
                    ])
            if io_data:
                print(tabulate(io_data,
                              headers=["Thiết bị", "Tổng Bytes đọc", "Số lần đọc", "Tổng Bytes ghi", "Số lần ghi"],
                              tablefmt="pretty", floatfmt=",.0f")) # floatfmt để định dạng số lần đọc/ghi
            else:
                print("Không có dữ liệu I/O phù hợp với các phân vùng đã hiển thị.")
        else:
            print("\nKhông thể lấy thông tin I/O.")


def display_large_files(large_files_list):
    """Hiển thị danh sách file lớn dưới dạng bảng."""
    if not large_files_list:
        logger.info("Không tìm thấy file lớn nào thỏa mãn điều kiện.")
        return
    
    print(f"\n=== TOP {len(large_files_list)} FILE LỚN NHẤT ===")
    file_data = []
    for filepath, size in large_files_list:
        try:
            # Sử dụng stat để lấy mtime chính xác hơn và kiểm tra file còn tồn tại
            stat_result = os.stat(filepath)
                modified_time = datetime.datetime.fromtimestamp(stat_result.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except FileNotFoundError:
            modified_time = "Đã xóa?"
        except OSError as e:
            logger.warning(f"Không thể lấy thời gian sửa đổi cho {filepath}: {e}")
            modified_time = "Lỗi khi đọc"    




                




    

