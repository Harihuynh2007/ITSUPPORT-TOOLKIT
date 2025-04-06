#!/usr/bin/env python3
"""
Script để kiểm tra và giám sát tình trạng CPU.
"""

import psutil
import time
import datetime
import argparse
import os
import sys
import logging

# Cấu hình logging cơ bản ra console cho các lỗi trong quá trình thiết lập
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_cpu_usage(interval=1.0, per_cpu=False):
    """
    Lấy phần trăm sử dụng CPU.

    Args:
        interval (float): Khoảng thời gian (giây) để tính toán mức sử dụng CPU.
                          Giá trị 0.0 hoặc None so sánh tức thì thời gian CPU
                          (trả về khác biệt so với lần gọi cuối hoặc khi import module).
                          Khuyến nghị sử dụng một khoảng thời gian nhỏ (ví dụ: 0.1 trở lên)
                          để có ảnh chụp nhanh đại diện hơn.
        per_cpu (bool): Nếu True, trả về danh sách phần trăm sử dụng cho mỗi lõi CPU.
                        Nếu False, trả về một số float cho tổng mức sử dụng CPU.

    Returns:
        float or list[float]: Phần trăm sử dụng CPU.
    """
    # Sử dụng interval > 0 là một lời gọi chặn (blocking) nhưng cho kết quả trung bình
    # chính xác hơn trong khoảng thời gian đó.
    return psutil.cpu_percent(interval=interval, percpu=per_cpu)

def get_cpu_info():
    """
    Lấy thông tin chi tiết của CPU.

    Returns:
        dict: Một dictionary chứa số lượng lõi CPU và thông tin tần số (nếu có).
              Trả về None cho các giá trị tần số nếu không thể xác định được.
    """
    cpu_info = {
        "physical_cores": None,
        "total_cores": None,
        "max_frequency": None,
        "current_frequency": None,
        "min_frequency": None
    }
    try:
        cpu_info["physical_cores"] = psutil.cpu_count(logical=False)
        cpu_info["total_cores"] = psutil.cpu_count(logical=True)
    except Exception as e:
        logging.warning(f"Không thể lấy số lượng lõi CPU: {e}")

    try:
        # Lấy tần số CPU (có thể yêu cầu quyền cụ thể hoặc không được hỗ trợ)
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            cpu_info["max_frequency"] = cpu_freq.max
            cpu_info["current_frequency"] = cpu_freq.current
            cpu_info["min_frequency"] = cpu_freq.min
    except NotImplementedError:
        logging.warning("Thông tin tần số CPU không có sẵn trên nền tảng này.")
    except Exception as e:
        logging.warning(f"Không thể lấy tần số CPU: {e}")

    return cpu_info

def setup_logger(log_file):
    """Thiết lập logging vào một file được chỉ định."""
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
            logging.info(f"Đã tạo thư mục log: {log_dir}")
        except OSError as e:
            logging.error(f"Không thể tạo thư mục log {log_dir}: {e}")
            return None # Không thể tiếp tục ghi log vào file

    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8') # Thêm encoding='utf-8'
    file_formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)

    logger = logging.getLogger('CPUMonitor')
    logger.setLevel(logging.INFO)
    # Tránh thêm handler nhiều lần nếu hàm được gọi lại (mặc dù không mong đợi ở đây)
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename for h in logger.handlers):
        logger.addHandler(file_handler)
        # Ngăn không cho lan truyền log lên logger gốc (ghi ra console)
        logger.propagate = False

    # Chỉ trả về logger để sử dụng
    return logger


def monitor_cpu(duration=60, interval=5, threshold=80, log_file=None, per_cpu=False):
    """
    Giám sát việc sử dụng CPU trong một khoảng thời gian xác định.

    Args:
        duration (int): Thời gian giám sát (giây).
        interval (int): Thời gian giữa các lần kiểm tra (giây). Phải > 0.
        threshold (int): Ngưỡng cảnh báo sử dụng CPU (%).
        log_file (str, optional): Đường dẫn đến file log. Mặc định là None (không ghi log file).
        per_cpu (bool): Có giám sát và ghi log cho từng lõi CPU hay không.
    """
    if interval <= 0:
        print("Lỗi: Khoảng thời gian giám sát phải lớn hơn 0.", file=sys.stderr)
        sys.exit(1)
    if duration <= 0:
        print("Lỗi: Thời gian giám sát phải lớn hơn 0.", file=sys.stderr)
        sys.exit(1)

    end_time = time.time() + duration
    alerts = 0

    # Thiết lập file logger nếu được chỉ định
    file_logger = None
    if log_file:
        file_logger = setup_logger(log_file)
        if not file_logger:
            print(f"Cảnh báo: Tiếp tục mà không ghi log file do lỗi thiết lập.", file=sys.stderr)


    print(f"Bắt đầu giám sát CPU trong {duration} giây...")
    print(f"Khoảng thời gian kiểm tra: {interval} giây, Ngưỡng cảnh báo: {threshold}%")
    if per_cpu:
        print("Giám sát mức sử dụng từng lõi.")
    if file_logger:
        print(f"Ghi log vào: {log_file}")
        file_logger.info(f"--- Giám sát CPU bắt đầu (Ngưỡng: {threshold}%) ---")

    try:
        while time.time() < end_time:
            # Sử dụng interval=0.1 (hoặc giá trị nhỏ tương tự) cho psutil để lấy ảnh chụp nhanh.
            # Việc điều chỉnh tốc độ chính được xử lý bởi time.sleep().
            # Sử dụng interval=interval trong psutil sẽ làm vòng lặp mất khoảng interval*2 giây.
            current_usage = get_cpu_usage(interval=0.1, per_cpu=per_cpu) # Interval ngắn để lấy snapshot
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            log_messages = []

            if per_cpu:
                core_alerts = 0
                usage_str_parts = []
                # Đảm bảo current_usage là list khi per_cpu=True
                if not isinstance(current_usage, list):
                     print(f"Lỗi: Không nhận được danh sách sử dụng từng core.", file=sys.stderr)
                     # Có thể thử lại hoặc bỏ qua lần này
                     time.sleep(interval)
                     continue

                for i, percent in enumerate(current_usage):
                    core_status = "Bình thường" # "OK"
                    if percent >= threshold:
                        core_status = "CẢNH BÁO" # "ALERT"
                        core_alerts += 1
                    usage_str_parts.append(f"Lõi {i}: {percent:.1f}% ({core_status})")

                overall_status = "CẢNH BÁO" if core_alerts > 0 else "Bình thường" # "ALERT" if core_alerts > 0 else "OK"
                usage_str = ", ".join(usage_str_parts)
                message = f"[{timestamp}] Sử dụng từng lõi: {usage_str} - Tổng thể: {overall_status}"
                if core_alerts > 0:
                    alerts += 1 # Đếm khoảng thời gian này là có cảnh báo nếu bất kỳ lõi nào cao
                log_messages.append(message)
                print(message) # In trạng thái chi tiết từng lõi

            else: # Tổng mức sử dụng CPU
                total_percent = current_usage
                status = "Bình thường" # "OK"
                if total_percent >= threshold:
                    status = "CẢNH BÁO" # "ALERT"
                    alerts += 1

                message = f"[{timestamp}] Tổng sử dụng CPU: {total_percent:.1f}% - Trạng thái: {status}"
                log_messages.append(message)
                print(message)

            # Ghi thông điệp log vào file nếu logger đang hoạt động
            if file_logger:
                for msg in log_messages:
                   # Xóa tiền tố timestamp [YYYY-MM-DD HH:MM:SS] khỏi msg vì logger tự thêm timestamp của nó
                   log_msg_content = msg.split("] ", 1)[1]
                   file_logger.info(log_msg_content)

            # Tính toán thời gian ngủ chính xác
            current_loop_time = time.time()
            time_spent = current_loop_time % interval
            sleep_time = interval - time_spent

            # Đảm bảo thời gian ngủ không âm hoặc quá nhỏ
            sleep_time = max(0.1, sleep_time)

            # Kiểm tra xem thời gian còn lại có ít hơn thời gian ngủ không
            remaining_time = end_time - current_loop_time
            if remaining_time <= 0:
                 break # Đã hết giờ
                 
            # Ngủ cho đến lần kiểm tra tiếp theo, nhưng không vượt quá thời gian còn lại
            actual_sleep = min(sleep_time, remaining_time)
            time.sleep(actual_sleep)


    except KeyboardInterrupt:
        print("\nGiám sát bị người dùng ngắt.")
    finally:
        summary = f"\nKết thúc giám sát CPU. Tổng số lần kiểm tra có cảnh báo: {alerts}"
        print(summary)
        if file_logger:
            file_logger.info(f"--- Giám sát CPU kết thúc ---")
            file_logger.info(f"Tổng số lần kiểm tra có cảnh báo: {alerts}")
            # Dọn dẹp các handler logging để đóng file đúng cách
            # (logging module thường tự xử lý khi chương trình kết thúc, nhưng có thể làm rõ ràng)
            for handler in list(file_logger.handlers): # Dùng list copy để tránh thay đổi dict đang duyệt
                handler.close()
                file_logger.removeHandler(handler)


def display_cpu_info(show_per_cpu=False):
    """Lấy và in thông tin CPU và mức sử dụng hiện tại."""
    cpu_info = get_cpu_info()
    print("=== Thông tin CPU ===")
    if cpu_info["physical_cores"] is not None:
        print(f"Số lõi vật lý: {cpu_info['physical_cores']}")
    if cpu_info["total_cores"] is not None:
        print(f"Tổng số lõi (Luồng xử lý): {cpu_info['total_cores']}")

    if cpu_info["max_frequency"] is not None:
        print(f"Tần số tối đa: {cpu_info['max_frequency']:.2f} MHz")
    if cpu_info["min_frequency"] is not None:
        print(f"Tần số tối thiểu: {cpu_info['min_frequency']:.2f} MHz")
    if cpu_info["current_frequency"] is not None:
        print(f"Tần số hiện tại: {cpu_info['current_frequency']:.2f} MHz")
    else:
         print("Thông tin tần số không có sẵn.")

    print("\n=== Mức sử dụng CPU hiện tại ===")
    # Sử dụng interval nhỏ để lấy snapshot nhanh
    usage_interval = 0.2

    if show_per_cpu:
        print("  Đang lấy mức sử dụng từng lõi...")
        try:
             # Lần gọi đầu có thể trả về 0.0, gọi lại sau một chút
             get_cpu_usage(interval=0.1, per_cpu=True) # Lần gọi khởi tạo
             time.sleep(usage_interval)
             cpu_percents = get_cpu_usage(interval=None, per_cpu=True) # Lấy mức sử dụng từ lần gọi trước
             if isinstance(cpu_percents, list):
                 for i, percent in enumerate(cpu_percents):
                     print(f"  Lõi {i}: {percent:.1f}%")
             else: # Phương án dự phòng nếu per_cpu vì lý do nào đó thất bại
                 print(f"  Tổng thể: {cpu_percents:.1f}%")
                 print("  (Không thể lấy mức sử dụng từng lõi)")
        except Exception as e:
            print(f"  Lỗi khi lấy mức sử dụng CPU từng lõi: {e}")

    print("  Đang lấy tổng mức sử dụng CPU...")
    try:
        # Lấy tổng mức sử dụng
        get_cpu_usage(interval=0.1, per_cpu=False) # Lần gọi khởi tạo
        time.sleep(usage_interval)
        total_percent = get_cpu_usage(interval=None, per_cpu=False) # Lấy mức sử dụng từ lần gọi trước
        print(f"Tổng sử dụng CPU: {total_percent:.1f}%")

        # Kiểm tra ngưỡng đơn giản để hiển thị ngay lập tức
        if total_percent >= 80:
            print("CẢNH BÁO: Mức sử dụng CPU cao!")
    except Exception as e:
        print(f"  Lỗi khi lấy tổng mức sử dụng CPU: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Công cụ giám sát và phân tích CPU.",
        epilog="Ví dụ: python cpu_monitor.py -m -d 300 -n 10 -t 90 -l /var/log/cpu_usage.log -p"
    )

    # Các tham số dòng lệnh
    parser.add_argument("-i", "--info", action="store_true",
                        help="Hiển thị thông tin chi tiết CPU và mức sử dụng hiện tại.")
    parser.add_argument("-m", "--monitor", action="store_true",
                        help="Giám sát mức sử dụng CPU trong một khoảng thời gian.")
    parser.add_argument("-d", "--duration", type=int, default=60,
                        help="Thời gian giám sát (giây) (mặc định: 60). Dùng với -m.")
    parser.add_argument("-n", "--interval", type=int, default=5,
                        help="Khoảng thời gian giữa các lần kiểm tra (giây) (mặc định: 5). Dùng với -m.")
    parser.add_argument("-t", "--threshold", type=int, default=80,
                        help="Ngưỡng cảnh báo sử dụng CPU (%) (mặc định: 80). Dùng với -m.")
    parser.add_argument("-l", "--log", metavar="FILE",
                        help="Đường dẫn đến file log để ghi kết quả giám sát. Dùng với -m.")
    parser.add_argument("-p", "--per-cpu", action="store_true",
                        help="Hiển thị/Giám sát mức sử dụng cho từng lõi CPU riêng biệt.")

    args = parser.parse_args()

    # Hành động mặc định: Nếu không có hành động cụ thể (-i hoặc -m) được yêu cầu, hiển thị thông tin cơ bản và mức sử dụng.
    if not args.info and not args.monitor:
        print("Không có hành động cụ thể nào được yêu cầu. Hiển thị thông tin mặc định và mức sử dụng hiện tại.")
        print("Sử dụng -i để xem thông tin chi tiết, -m để giám sát, hoặc --help để xem các tùy chọn.\n")
        display_cpu_info(show_per_cpu=args.per_cpu) # Sử dụng per_cpu nếu được chỉ định ngay cả trong chế độ mặc định
        sys.exit(0)

    # Hiển thị thông tin chi tiết
    if args.info:
        display_cpu_info(show_per_cpu=args.per_cpu)

    # Giám sát CPU
    if args.monitor:
        # Thêm dấu phân cách nếu thông tin cũng đã được hiển thị
        if args.info:
            print("\n" + "="*20 + "\n")

        monitor_cpu(
            duration=args.duration,
            interval=args.interval,
            threshold=args.threshold,
            log_file=args.log,
            per_cpu=args.per_cpu
        )

if __name__ == "__main__":
    # Đảm bảo stdout hỗ trợ UTF-8 (quan trọng cho tiếng Việt trên một số terminal/OS)
    if sys.stdout.encoding != 'utf-8':
         try:
             # Cố gắng đặt encoding thành UTF-8
             sys.stdout.reconfigure(encoding='utf-8')
             sys.stderr.reconfigure(encoding='utf-8')
         except Exception as e:
              print(f"Cảnh báo: Không thể đặt encoding của stdout/stderr thành UTF-8: {e}", file=sys.stderr)
              print("Output có thể hiển thị không chính xác.", file=sys.stderr)
    main()