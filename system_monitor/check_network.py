#!/usr/bin/env python3
"""
Network Monitoring Tool - Kiem tra cac thong so mang
Phan cua Bo cong cu ho tro IT Support

Yeu cau cai dat thu vien: pip install psutil
"""

import os
import socket
import subprocess
import time
import platform
import re # Them module re de phan tich output ping
from datetime import datetime

# Thu kiem tra xem psutil da duoc cai dat chua
try:
    import psutil
except ImportError:
    print("Loi: Thu vien 'psutil' chua duoc cai dat.")
    print("Vui long chay: pip install psutil")
    exit()

def check_connection(host="8.8.8.8", port=53, timeout=3):
    """Kiem tra ket noi internet bang cach ket noi den Google DNS"""
    try:
        socket.setdefaulttimeout(timeout)
        # Su dung AF_INET de dam bao chi kiem tra IPv4
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as e:
        # Ghi log loi cu the (tuy chon)
        # print(f"Loi ket noi: {e}")
        return False

def get_ping_stats(host="8.8.8.8", count=4):
    """
    Lay thong ke ping va phan tich ket qua.
    Tra ve mot dictionary chua cac thong so hoac None neu loi.
    """
    system = platform.system().lower()
    command = []
    try:
        if system == "windows":
            command = ["ping", "-n", str(count), host]
        else:  # Linux va macOS
            command = ["ping", "-c", str(count), host]

        # Tang timeout cho subprocess de tranh bi treo neu ping lau
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        output, error = process.communicate(timeout=15) # Timeout 15 giay

        if process.returncode != 0:
             # Neu co loi stderr, in ra de debug
            if error:
                # print(f"Loi ping stderr: {error.strip()}")
                # Co the tra ve loi cu the hon neu can
                return {"error": f"Ping command failed with error: {error.strip()}"}
            return {"error": f"Khong the ping den may chu {host}. Ma loi: {process.returncode}"}

        # Phan tich output de lay thong tin chi tiet
        stats = {"host": host}
        if system == "windows":
            loss_match = re.search(r"Lost = (\d+) \((\d+)% loss\)", output)
            # Tim dong chua thong ke RTT (co the khac nhau tuy ngon ngu he thong)
            rtt_match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", output) \
                     or re.search(r"Thoi gian di ve vong nho nhat = (\d+)ms, Lon nhat = (\d+)ms, Trung binh = (\d+)ms", output) # Tieng Viet

            if loss_match:
                stats["packets_sent"] = count
                stats["packets_lost"] = int(loss_match.group(1))
                stats["packet_loss_percent"] = int(loss_match.group(2))
                stats["packets_received"] = count - stats["packets_lost"]
            if rtt_match:
                stats["min_rtt"] = int(rtt_match.group(1))
                stats["max_rtt"] = int(rtt_match.group(2))
                stats["avg_rtt"] = int(rtt_match.group(3))
        else: # Linux / macOS
            loss_match = re.search(r"(\d+) packets transmitted, (\d+) received,.*? (\d+)% packet loss", output)
            rtt_match = re.search(r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms", output)

            if loss_match:
                stats["packets_sent"] = int(loss_match.group(1))
                stats["packets_received"] = int(loss_match.group(2))
                stats["packet_loss_percent"] = int(loss_match.group(3))
                stats["packets_lost"] = stats["packets_sent"] - stats["packets_received"]
            if rtt_match:
                stats["min_rtt"] = float(rtt_match.group(1))
                stats["avg_rtt"] = float(rtt_match.group(2))
                stats["max_rtt"] = float(rtt_match.group(3))

        # Neu khong phan tich duoc gi, tra ve output tho
        if len(stats) <= 1: # Chi co 'host'
             return {"raw_output": output.strip()} # Tra ve output tho neu khong phan tich duoc

        return stats

    except subprocess.TimeoutExpired:
        return {"error": f"Lenh ping toi {host} vuot qua thoi gian cho (15s)"}
    except FileNotFoundError:
        return {"error": "Loi: Khong tim thay lenh 'ping'. Kiem tra PATH."}
    except Exception as e:
        # Ghi log loi cu the (tuy chon)
        # print(f"Loi khong mong doi khi ping: {e}")
        return {"error": f"Loi khong mong doi khi ping: {e}"}


def get_network_interfaces():
    """Lay thong tin ve cac giao dien mang va dia chi IP cua chung"""
    interfaces = {}
    try:
        all_interfaces = psutil.net_if_addrs()
        for interface, addrs in all_interfaces.items():
            interfaces[interface] = []
            for addr in addrs:
                # Bo qua dia chi link-local (fe80::) cho IPv6 de gon hon
                if addr.family == socket.AF_INET:  # IPv4
                    interfaces[interface].append(f"IPv4: {addr.address} (Netmask: {addr.netmask})")
                elif addr.family == socket.AF_INET6 and not addr.address.startswith('fe80::'):  # IPv6
                    interfaces[interface].append(f"IPv6: {addr.address}")
                # Co the them MAC address neu can:
                # elif addr.family == psutil.AF_LINK:
                #    interfaces[interface].append(f"MAC: {addr.address}")
    except Exception as e:
        print(f"Loi khi lay thong tin giao dien mang: {e}")
    return interfaces

def get_network_stats():
    """Lay thong ke ve luu luong mang"""
    try:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
            "dropin": net_io.dropin,
            "dropout": net_io.dropout
        }
    except Exception as e:
        print(f"Loi khi lay thong ke luu luong mang: {e}")
        return None # Tra ve None neu co loi

def get_network_connections():
    """Liet ke cac ket noi mang dang hoat dong (TCP established)"""
    connections = []
    try:
        for conn in psutil.net_connections(kind='inet'): # 'inet' bao gom ca tcp va udp, ipv4 va ipv6
            # Loc chi cac ket noi TCP da thiet lap (ESTABLISHED)
            if conn.type == socket.SOCK_STREAM and conn.status == psutil.CONN_ESTABLISHED:
                process_name = "N/A" # Gia tri mac dinh
                if conn.pid: # Chi lay ten process neu co PID
                    try:
                        process = psutil.Process(conn.pid)
                        process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_name = "Khong truy cap duoc" # Hoac process da ket thuc
                    except psutil.ZombieProcess:
                        process_name = "Zombie Process"

                # Xu ly truong hop raddr khong ton tai (hiem khi voi ESTABLISHED)
                remote_addr_str = "N/A"
                if conn.raddr and conn.raddr.ip and conn.raddr.port:
                   remote_addr_str = f"{conn.raddr.ip}:{conn.raddr.port}"

                connections.append({
                    "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}",
                    "remote_addr": remote_addr_str,
                    "status": conn.status, # Luon la ESTABLISHED o day
                    "process": process_name,
                    "pid": conn.pid if conn.pid else "N/A"
                })
    except psutil.AccessDenied:
        print("Loi: Khong co quyen truy cap thong tin ket noi mang (can chay voi quyen admin/root?).")
    except Exception as e:
        print(f"Loi khi lay thong tin ket noi mang: {e}")
    return connections

def get_open_ports(host='127.0.0.1', start_port=1, end_port=1024, timeout=0.2):
    """
    Kiem tra cac cong TCP mo tren mot host (mac dinh la localhost).
    Tang timeout de giam kha nang bao loi sai (false negative).
    """
    open_ports = []
    # print(f"Dang quet cong tu {start_port} den {end_port} tren {host}...")
    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout) # Tang timeout len mot chut
        # Su dung connect_ex thay vi connect de khong nem ra exception khi cong dong
        result = sock.connect_ex((host, port))
        if result == 0: # Cong mo
            try:
                # Co gang lay ten dich vu tuong ung voi cong
                service = socket.getservbyport(port, 'tcp') # Chi dinh ro 'tcp'
            except (OSError, socket.error):
                # Neu khong tim thay ten dich vu pho bien
                service = "unknown"
            open_ports.append((port, service))
        sock.close() # Dong socket sau moi lan kiem tra
    return open_ports

def format_bytes(b):
    """Chuyen doi bytes thanh don vi doc duoc (KB, MB, GB)"""
    if b is None: return "N/A" # Xu ly truong hop input la None
    try:
        b = float(b)
        if b < 0: return "N/A" # Xu ly gia tri am bat thuong
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']:
            if abs(b) < 1024.0:
                return f"{b:3.2f} {unit}"
            b /= 1024.0
        return f"{b:.2f} YB" # Neu qua lon
    except (ValueError, TypeError):
        return "N/A" # Xu ly neu input khong phai so

def print_separator(char="=", length=50):
    """In ra dong phan cach"""
    print(char * length)

def main():
    """Ham chinh dieu khien luong thuc thi"""
    print_separator()
    print("CONG CU KIEM TRA MANG")
    print_separator()

    # Thoi gian hien tai
    now = datetime.now()
    print(f"Thoi gian kiem tra: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Kiem tra ket noi internet
    print("\n--- 1. Kiem tra ket noi Internet ---")
    if check_connection():
        print("   [✓] Ket noi Internet: Thanh cong (kiem tra qua Google DNS)")

        # 2. Thong so Ping (chi thuc hien neu co internet)
        print("\n--- 2. Thong so Ping (toi 8.8.8.8) ---")
        ping_result = get_ping_stats() # Ping toi Google DNS
        if ping_result:
            if "error" in ping_result:
                print(f"   [✗] Loi Ping: {ping_result['error']}")
            elif "raw_output" in ping_result:
                 print(f"   [!] Khong the phan tich chi tiet output ping. Output tho:")
                 print(f"     {ping_result['raw_output']}")
            else:
                print(f"   [✓] Ping toi {ping_result['host']}:")
                print(f"       - Thoi gian phan hoi (RTT): Min={ping_result.get('min_rtt', 'N/A')}ms, Avg={ping_result.get('avg_rtt', 'N/A')}ms, Max={ping_result.get('max_rtt', 'N/A')}ms")
                print(f"       - Goi tin: Gui={ping_result.get('packets_sent', 'N/A')}, Nhan={ping_result.get('packets_received', 'N/A')}, Mat={ping_result.get('packets_lost', 'N/A')} ({ping_result.get('packet_loss_percent', 'N/A')}%)")
        else:
            print("   [✗] Khong nhan duoc ket qua ping.")

    else:
        print("   [✗] Ket noi Internet: That bai")
        print("\n--- 2. Thong so Ping ---")
        print("   [!] Bo qua kiem tra ping do khong co ket noi Internet.")

    # 3. Thong tin ve giao dien mang
    print("\n--- 3. Giao dien mang ---")
    interfaces = get_network_interfaces()
    if interfaces:
        for interface, addresses in interfaces.items():
            # In ten interface noi bat hon
            print(f"\n   Interface: {interface}")
            if addresses:
                for addr in addresses:
                    print(f"     - {addr}")
            else:
                print("     (Khong co dia chi IP duoc cau hinh)")
    else:
        print("   [!] Khong the lay thong tin giao dien mang.")

    # 4. Thong ke luu luong mang
    print("\n--- 4. Thong ke luu luong mang (Tong cong) ---")
    stats = get_network_stats()
    if stats:
        print(f"   - Du lieu da gui: {format_bytes(stats.get('bytes_sent'))} ({format_bytes(stats.get('packets_sent'))} goi)")
        print(f"   - Du lieu da nhan: {format_bytes(stats.get('bytes_recv'))} ({format_bytes(stats.get('packets_recv'))} goi)")
        print(f"   - Loi vao/ra: {stats.get('errin', 'N/A')} / {stats.get('errout', 'N/A')}")
        print(f"   - Goi bi huy vao/ra: {stats.get('dropin', 'N/A')} / {stats.get('dropout', 'N/A')}")
    else:
        print("   [!] Khong the lay thong ke luu luong mang.")

    # 5. Liet ke ket noi TCP dang hoat dong
    print("\n--- 5. Ket noi TCP dang hoat dong (Established) ---")
    connections = get_network_connections()
    if connections:
        print(f"   Tim thay {len(connections)} ket noi:")
        # Hien thi toi da 15 ket noi de tranh tran man hinh
        display_limit = 15
        for i, conn in enumerate(connections[:display_limit], 1):
            print(f"   {i}. Local: {conn['local_addr']:<22} -> Remote: {conn['remote_addr']:<22} | Process: {conn['process']} (PID: {conn['pid']})")
        if len(connections) > display_limit:
            print(f"   ... va {len(connections) - display_limit} ket noi khac.")
    elif connections is not None: # Neu ham tra ve list rong (khong co loi)
         print("   [i] Khong co ket noi TCP nao dang o trang thai ESTABLISHED.")
    # Neu connections la None thi loi da duoc in ra trong ham get_network_connections

    # 6. Kiem tra cac cong mo tren localhost (pham vi nho de nhanh)
    print("\n--- 6. Kiem tra cong TCP mo tren Localhost (Cong 1-100) ---")
    try:
        # Chi quet tren localhost (127.0.0.1) va pham vi cong nho (1-100) de tranh cham
        open_ports = get_open_ports(host='127.0.0.1', start_port=1, end_port=100, timeout=0.1) # Giam timeout lai cho nhanh
        if open_ports:
            print("   [✓] Cac cong TCP mo tim thay:")
            port_list = []
            for port, service in open_ports:
                port_list.append(f"{port} ({service})")
            # In thanh hang ngang cho gon
            print("     " + ", ".join(port_list))
        else:
            print("   [i] Khong tim thay cong TCP mo nao trong pham vi 1-100 tren localhost.")
    except Exception as e:
        print(f"   [✗] Loi khi quet cong: {e}")

    print_separator()
    print("Ket thuc kiem tra.")
    print_separator()

if __name__ == "__main__":
    # Kiem tra quyen admin/root (quan trong cho net_connections)
    try:
        # Tren Windows, kiem tra quyen admin
        if platform.system() == "Windows":
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("\n[CANH BAO] Ban dang khong chay voi quyen Administrator.")
                print("   Mot so thong tin (vi du: process cua ket noi mang) co the khong hien thi duoc.")
        # Tren Linux/macOS, kiem tra user ID (0 la root)
        elif os.geteuid() != 0:
            print("\n[CANH BAO] Ban dang khong chay voi quyen root/sudo.")
            print("   Mot so thong tin (vi du: process cua ket noi mang) co the khong hien thi duoc.")
    except AttributeError:
         # os.geteuid khong ton tai tren mot so he thong (vi du Windows khong co WSL)
         pass
    except ImportError:
        # ctypes khong co san (hiem)
        pass

    main()