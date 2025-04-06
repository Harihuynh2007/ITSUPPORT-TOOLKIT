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
def display_memory_info(show_swap=True, show_top_procs=False, num_top_procs=5):
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

            # Kiểm tra ngưỡng RAM
            if ram['percent'] >= ram_threshold:
                ram_status = f"\033[91mCẢNH BÁO ({ram['percent']:.1f}%)\033[0m"
                alerts_ram_count += 1
                is_alert = True
                alert_messages.append(f"RAM usage {ram['percent']:.1f}% >= {ram_threshold}%")
                    
            # Kiểm tra ngưỡng SWAP (chỉ khi SWAP tồn tại)
            if swap['total'] > 0 and swap['percent'] >= swap_threshold:
                swap_status = f"\033[93mCẢNH BÁO ({swap['percent']:.1f}%)\033[0m" # Màu vàng
                alerts_swap_count += 1
                is_alert = True
                alert_messages.append(f"SWAP usage {swap['percent']:.1f}% >= {swap_threshold}%")

            # Tạo message log/print
            # Hiển thị RAM: Used/Total (Percent) | SWAP: Used/Total (Percent) - Status    
            ram_str = f"RAM: {get_size(ram['used'])}/{get_size(ram['total'])} ({ram['percent']:.1f}%)"
            swap_str = f"SWAP: {get_size(swap['used'])}/{get_size(swap['total'])} ({swap['percent']:.1f}%)" if swap['total'] > 0 else "SWAP: N/A"
            status_str = f"RAM: {ram_status}, SWAP: {swap_status}" if swap['total'] > 0 else f"RAM: {ram_status}"

            message = f"[{timestamp}] {ram_str} | {swap_str} | Status: {status_str}"
            print(message)

            # Ghi log
            if log_handle :
                log_ram_status = f"CẢNH BÁO ({ram['percent']:.1f}%)" if ram['percent'] >= ram_threshold else "OK"
                log_swap_status = f"CẢNH BÁO ({swap['percent']:.1f}%)" if swap['total'] > 0 and swap['percent'] >= swap_threshold else "OK"
                log_status_str = f"RAM: {log_ram_status}, SWAP: {log_swap_status}" if swap['total'] > 0 else f"RAM: {log_ram_status}"
                log_message = f"[{timestamp}] {ram_str} | {swap_str} | Status : { log_status_str}\n"
                log_handle.write(log_message)


            # --- Bổ sung: Hiển thị top process khi có cảnh báo ---
            if is_alert and show_procs_on_alert:
                top_processes = get_top_processes(num_top_procs)
                if top_processes:
                    proc_alert_healer = f"  -> Top {len(top_processes)} process gây tải ({', '.join(alert_messages)}):"
                    print(proc_alert_healer)
                if log_handle:
                    log_handle.write(proc_alert_healer + "\n")
                for i, proc in enumerate(top_processes):
                    proc_line = f"     {i+1}. {proc.get('name', 'N/A')} (PID: {proc.get('pid', 'N/A')}) - {proc.get('memory_percent', 0):.2f}% RAM"
                    print(proc_line)
                    if log_handle:
                        log_handle.write(proc_line + "\n")
                else:
                    print("> Không thể lấy thông tin process khi cảnh báo.")      
                    if log_handle:
                        log_handle.write("> Không thể lấy thông tin process khi cảnh báo.\n")


            if log_handle:
                log_handle.flush()

            # Ngủ đến lần kiểm tra tiếp theo
            # Tính toán thời gian ngủ chính xác hơn để bù đắp thời gian xử lý
            elapsed = time.time() - start_time
            remaining_interval = interval - (elapsed % interval)
            time.sleep(max(0.1, remaining_interval))   

    except KeyboardInterrupt:
        print("\nĐã dừng giám sát bởi người dùng.")        
    finally:
        # Tổng kết
        summary = f"\n--- Kết thúc giám sát lúc {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---"
        summary += f"\nTổng số cảnh báo RAM: {alerts_ram_count}"
        summary += f"\nTổng số cảnh báo SWAP: {alerts_swap_count}"
        print(summary)

        if log_handle:
            log_handle.write(summary + "\n")
            log_handle.close()
            print(f"Đã ghi log chi tiết vào: {log_file}")
        print("-" * 30)    


# --- Hàm chính ---
def main():
    parser = argparse.ArgumentParser(
        description="Công cụ giám sát và phân tích RAM & SWAP.",
        formatter_class=argparse.RawTextHelpFormatter # Giữ nguyên định dạng help message
    )

    # Nhóm Action (chọn 1 trong 2)
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "-i", "--info",
        action="store_true",
        help="Hiển thị thông tin chi tiết về RAM, SWAP và top process sử dụng RAM."
    )
    action_group.add_argument(
        "-m", "--monitor",
        action="store_true",
        help="Bật chế độ giám sát RAM và SWAP theo thời gian thực."
    )

    # Tùy chọn cho chế độ giám sát (--monitor)
    monitor_group = parser.add_argument_group('Tùy chọn giám sát (--monitor)')
    monitor_group.add_argument(
        "-d", "--duration",
        type=int, default=60, metavar='GIÂY',
        help="Thời gian giám sát (giây). Mặc định: 60"
    )
    monitor_group.add_argument(
        "-n", "--interval",
        type=int, default=5, metavar='GIÂY',
        help="Khoảng thời gian giữa các lần kiểm tra (giây). Mặc định: 5"
    )
    monitor_group.add_argument(
        "-t", "--ram-threshold",
        type=int, default=80, metavar='PHẦN_TRĂM',
        help="Ngưỡng cảnh báo sử dụng RAM (%%). Mặc định: 80"
    )
    monitor_group.add_argument(
        "--swap-threshold", # Đổi tên để rõ ràng hơn
        type=int, default=80, metavar='PHẦN_TRĂM',
        help="Ngưỡng cảnh báo sử dụng SWAP (%%). Mặc định: 80"
    )
    monitor_group.add_argument(
        "-l", "--log",
        metavar='ĐƯỜNG_DẪN_FILE',
        help="Đường dẫn đến file để ghi log giám sát."
    )
    monitor_group.add_argument(
        "--show-procs-on-alert",
        action="store_true",
        help="Hiển thị các process chiếm nhiều RAM nhất khi có cảnh báo."
    )
    monitor_group.add_argument(
        "--num-procs",
        type=int, default=3, metavar='SỐ_LƯỢNG',
        help="Số lượng process hiển thị khi có cảnh báo (dùng với --show-procs-on-alert). Mặc định: 3"
    )

    # Tùy chọn cho chế độ thông tin (--info)
    info_group = parser.add_argument_group('Tùy chọn thông tin (--info)')
    info_group.add_argument(
        "--num-top-procs",
        type=int, default=5, metavar='SỐ_LƯỢNG',
        help="Số lượng top process hiển thị trong chế độ thông tin. Mặc định: 5"
    )


    # --- Bổ sung: Xử lý trường hợp không có tham số nào ---
    # Nếu không có tham số nào được cung cấp, in trợ giúp và thoát
    if len(sys.argv) == 1:
        # Hiển thị thông tin cơ bản làm mặc định thay vì in help
        print("Chạy không có tham số, hiển thị thông tin cơ bản (tương đương --info):")
        display_memory_info(show_swap=True, show_top_procs=True, num_top_procs=5) # Hiển thị cả top 5 process mặc định
        # parser.print_help(sys.stderr) # Hoặc có thể in help
        sys.exit(0)


    args = parser.parse_args()    

    # --- Logic thực thi ---
    if args.monitor:
        # --- Bổ sung: Validation input cho monitor ---
        if args.duration <= 0:
            parser.error("Thời gian giám sát (--duration) phải lớn hơn 0.")
        if args.interval <= 0:
             parser.error("Khoảng cách kiểm tra (--interval) phải lớn hơn 0.")
        if not (0 < args.ram_threshold <= 100):
             parser.error("Ngưỡng RAM (--ram-threshold) phải trong khoảng (0, 100].")
        if not (0 < args.swap_threshold <= 100):
             parser.error("Ngưỡng SWAP (--swap-threshold) phải trong khoảng (0, 100].")
        if args.num_procs <= 0:
             parser.error("Số lượng process (--num-procs) phải lớn hơn 0.")

        monitor_memory(
            duration=args.duration,
            interval=args.interval,
            ram_threshold=args.ram_threshold,
            swap_threshold=args.swap_threshold, # Sử dụng tham số mới
            log_file=args.log,
            show_procs_on_alert=args.show_procs_on_alert, # Thêm tham số mới
            num_top_procs=args.num_procs # Thêm tham số mới
        )
    elif args.info:
         # --- Bổ sung: Validation input cho info ---
         if args.num_top_procs <= 0:
             parser.error("Số lượng top process (--num-top-procs) phải lớn hơn 0.")

         display_memory_info(show_swap=True, show_top_procs=True, num_top_procs=args.num_top_procs)


if __name__ == "__main__":
    main()         