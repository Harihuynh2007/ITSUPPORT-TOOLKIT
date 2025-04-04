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
    ram = memory_info['ram']
    print("[RAM]")
    print(f"  Tổng cộng : {get_size(ram['total'])}")
    print(f"  Đã dùng   : {get_size(ram['used'])} ({ram['percent']:.1f}%)")
    print(f"  Còn trống : {get_size(ram['available'])}")
    # Thêm cảnh báo trực tiếp ở đây nếu cần
    if ram['percent'] >= 80: # Ngưỡng mặc định nếu chỉ xem info
         print("  \033[91mCẢNH BÁO: Mức sử dụng RAM cao!\033[0m") # Màu đỏ

    # Thông tin SWAP
    if show_swap:
        swap= memory_info['swap']
        print("\n[SWAP]")
        if swap('total') > 0:   
            print(f"  Tổng cộng : {get_size(swap['total'])}")
            print(f"  Đã dùng   : {get_size(swap['used'])} ({swap['percent']:.1f}%)")
            print(f"  Còn trống : {get_size(swap['free'])}")
            # Thêm cảnh báo SWAP nếu cần
            if swap['percent'] >= 80: # Có thể đặt ngưỡng khác
                 print("  \033[93mCẢNH BÁO: Mức sử dụng SWAP cao!\033[0m") # Màu vàng
    else :
        print(" (Không có SWAP hoặc SWAP bị vô hiệu hóa)")        


    # Thông tin Top Processes
    if show_top_procs:
        print("\n" + "=" * 30)
        print(f" TOP {num_top_procs} PROCESS DÙNG NHIỀU RAM NHẤT")
        print("=" * 30)
        top_processes = get_top_processes(num_top_procs)
        if top_processes:
            for i  ,proc in enumerate(top_processes):
                print(f"  {i+1}. {proc.get['name', 'N/A']} (PID :{proc.get('pid', 'N/A')}) - {proc.get('memory_percent', 0):.2f}%")
        else:
            print("  Không thể lấy thông tin process.")   
    print("-" * 30)         

 
    # --- Hàm giám sát ---
    def monitor_memory(duration=60, interval = 5, ram_threshold=80, swap_threshold=80, log_file=None, show_procs_on_alert=False, num_top_procs=3):
        """
        Giám sát RAM và SWAP trong khoảng thời gian xác định, ghi log và cảnh báo.

        Args:
            duration (int): Thời gian giám sát (giây).
            interval (int): Khoảng thời gian giữa các lần kiểm tra (giây).
            ram_threshold (int): Ngưỡng cảnh báo sử dụng RAM (%).
            swap_threshold (int): Ngưỡng cảnh báo sử dụng SWAP (%).
            log_file (str): Đường dẫn file log (nếu có).
            show_procs_on_alert (bool): Hiển thị top process khi có cảnh báo.
            num_top_procs (int): Số process hiển thị khi có cảnh báo.
        """        
         
         
        if duration <= 0 or interval <= 0:
            print("Lỗi: Thời gian giám sát (duration) và khoảng cách (interval) phải lớn hơn 0.", file=sys.stderr)
            return
        if not ( 0 < ram_threshold <= 100 and 0 < swap_threshold <= 100):
            print("Lỗi: Ngưỡng (threshold) phải nằm trong khoảng (0, 100].", file=sys.stderr)
            return
    
        start_time = time.time()
        end_time = start_time + duration


        print(f"Bắt đầu giám sát Bộ nhớ (RAM > {ram_threshold}%, SWAP > {swap_threshold}%) trong {duration}s...")
        print(f"Kiểm tra mỗi {interval}s. Ghi log vào: {'Bật (' + log_file + ')' if log_file else 'Tắt'}")
        print("-" * 30)

        log_handle = None
        if log_file:
            try:
                # --- Bổ sung: Tạo thư mục nếu chưa tồn tại ---
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exits(log_dir):
                    os.makedirs(log_dir, exist_ok= True)# exist_ok=True để không báo lỗi nếu thư mục đã tồn tại
                log_handle = open(log_file, "a", encoding='utf-8')  
                log_handle.write(f"\n--- Giám sát Bộ nhớ bắt đầu lúc {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                log_handle.write(f"Ngưỡng RAM: {ram_threshold}%, Ngưỡng SWAP: {swap_threshold}%\n")  
            except IOError as e:
                # --- Bổ sung: Xử lý lỗi ghi log ---
                print(f"\n\033[91mLỗi khi mở file log '{log_file}': {e}\033[0m", file=sys.stderr)
                print("Giám sát sẽ tiếp tục mà không ghi log.")
                log_handle = None # Đảm bảo không cố ghi vào file bị lỗi

        alerts_ram_count = 0
        alerts_swap_count = 0
        try :
            while time.time() < end_time:
                mem_info = get_memory_info()
                if not mem_info:
                    time.sleep(interval)
                    continue

                ram = mem_info['ram']
                swap = mem_info['swap']
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                ram_status = 'OK'
                swap_status = 'OK'
                is_alert = False
                alert_messages = []
                        
                        