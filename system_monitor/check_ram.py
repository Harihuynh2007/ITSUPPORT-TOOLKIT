import time 
import datetime
import os
import sys

try:
    import psutil
except ImportError:
    print("Lỗi: Thư viện 'psutil' chưa được cài đặt.")
    print("Vui lòng cài đặt bằng lệnh: pip install psutil")
    sys.exit(1) # Thoát chương trình với mã lỗi

# --- Hàm tiện ích ---

def get_size(bytes_val, suffix= "B"):
    """
    Chuyển đổi đơn vị bytes sang định dạng dễ đọc (KB, MB, GB, TB,...).

    Args:
        bytes_val (int): Giá trị byte cần chuyển đổi.
        suffix (str): Hậu tố đơn vị (mặc định là "B").

    Returns:
        str: Chuỗi biểu diễn dung lượng đã định dạng.
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if abs(bytes_val) < factor: # Dùng abs để xử lý số âm (nếu có)
            return f"{bytes_val:.2f}{unit}{suffix}"
        bytes_val /= factor
    # Trường hợp số quá lớn (ít xảy ra với RAM/SWAP)
    return f"{bytes_val:.2f}E{suffix}"

# --- Hàm lấy thông tin ---
def get_memory_info():
    """
    Lấy thông tin chi tiết của RAM và SWAP.

    Returns:
        dict: Dictionary chứa thông tin RAM và SWAP, hoặc None nếu không lấy được.
    """

    try:
        svmem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        memory_info = {
            "ram": {
                "total": svmem.total,
                "available": svmem.available,
                "used": svmem.used,
                "percent": svmem.percent
            },
            "swap": {
                "total": swap.total,
                "free": swap.free,
                "used": swap.used,
                "percent": swap.percent
            }
        }
        return memory_info
    except Exception as e:
        print(f"Lỗi khi lấy thông tin bộ nhớ: {e}", file=sys.stderr)
        return None
    
def get_top_processes(num_processes=5):
    """
    Lấy danh sách các process sử dụng nhiều RAM nhất.

    Args:
        num_processes (int): Số lượng process cần lấy (mặc định là 5).

    Returns:
        list: Danh sách các dictionary chứa thông tin process (pid, name, memory_percent),
              hoặc danh sách rỗng nếu có lỗi.
    """   

    try :
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                # Lấy thông tin process
                proc_info = proc.info
                # Bỏ qua các process hệ thống không có memory_percent hoặc giá trị âm (ít gặp)
                if proc_info.get('memory_percent') is not None and proc_info['memory_percent'] >= 0:
                    processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Bỏ qua các process không truy cập được hoặc đã chết
                pass

        # Sắp xếp danh sách process theo mức độ sử dụng RAM giảm dần
        processes = sorted(processes, key=lambda p: p.get['memory_percent',0], reverse=True)

        return processes[:num_processes]
    except Exception as e:
        print(f"Lỗi khi lấy thông tin process: {e}", file=sys.stderr)
        return []     

def get_top_processess(num_processes=5):
    """
    Lấy danh sách các process sử dụng nhiều RAM nhất.

    Args:
        num_processes (int): Số lượng process cần lấy (mặc định là 5).

    Returns:
        list: Danh sách các dictionary chứa thông tin process (pid, name, memory_percent),
              hoặc danh sách rỗng nếu có lỗi.
    """

    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                # Lấy thông tin process
                proc_info = proc.info
                # Bỏ qua các process hệ thống không có memory_percent hoặc giá trị âm (ít gặp)
                if proc_info.get('memory_percent') is not None and proc_info['memory_percent'] >= 0:
                    processes.append(proc_info)
            except (psutil.NoSuckProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Bỏ qua các process không truy cập được hoặc đã chết
                pass        

        # Sắp xếp theo tỷ lệ sử dụng RAM giảm dần
        processes = sorted(processes, key=lambda p : p.get('memory_percemt'))    

        return processes[:num_processes]
    except Exception as e:
        print(f"Lỗi khi lấy thông tin process: {e}", file=sys.stderr)
        return[]
    
# --- Hàm hiển thị ---
def display_memory_info(show_swap=True, show_stop_procs=False, num_top_procs=5):
    """
    Hiển thị thông tin RAM và SWAP (tùy chọn), và top process (tùy chọn).

    Args:
        show_swap (bool): Có hiển thị thông tin SWAP hay không.
        show_top_procs (bool): Có hiển thị top process hay không.
        num_top_procs (int): Số lượng top process cần hiển thị.
    """

    memory_info = get_memory_info()
    if not memory_info:
        return
    
    print("=" * 30)
    print("      THÔNG TIN BỘ NHỚ")
    print("=" * 30)

    # Thông tin RAM
