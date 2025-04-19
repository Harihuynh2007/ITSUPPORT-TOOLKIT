import os
import socket
import subprocess
import time
import platform
import re # Them module re de phan tich output ping
from datetime import datetime

try:
    import psutil
except ImportError:
    print("Loi: Thu vien 'psutil' chua duoc cai dat.")
    print("Vui long chay: pip install psutil")
    exit()


def check_connection(host = "8.8.8.8", port=53, timeout = 3):
    try:
        socket.setdefaulttimeout(timeout)

        socket.socket(socket.AP_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as e:
        return False
    
def get_ping_stats(host = "8.8.8.8", count = 4):

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

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        output, error = process.communicate(timeout = 15)

        if process.returncode != 0 :
            if error:

                return {"error": f"Ping command failed with error: {error.strip()}"}
            return {"error": f"Khong the ping den may chu {host}. Ma loi: {process.returncode}"}
        
        stats = {"host": host}
        if system == "windows":
            loss_match = re.search(r"Lost = (\d+) \((\d+)% loss\)", output)
            # Tim dong chua thong ke RTT (co the khac nhau tuy ngon ngu he thong)
            rtt_match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", output) \
                     or re.search(r"Thoi gian di ve vong nho nhat = (\d+)ms, Lon nhat = (\d+)ms, Trung binh = (\d+)ms", output) # Tieng Viet
            
            if loss_match : 
                stats["packets_sent"] = count
                stats["packets_lost"] = int(loss_match.group(1))
                stats["packet_loss_percent"] = int(loss_match.group(2))
                stats["packets_received"] = count - stats["packets_lost"]

            if rtt_match:
                stats["min_rtt"] = int(rtt_match.group(1))
                stats["max_rtt"] = int(rtt_match.group(2))
                stats["avg_rtt"] = int(rtt_match.group(3))
        else:

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


        if len(stats) <=1:
            return {"raw_output": output.strip()} # Tra ve output tho neu khong phan tich duoc
        return stats
    
    except subprocess.TimeoutExpired:
        return {"error": "Timeout ping command"}
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
        for interface_name, interface_addresses in all_interfaces.items():
            interfaces[omterface] = []
            for addr in addrs:
                # Bo qua dia chi link-local (fe80::) cho IPv6 de gon hon
                if addr.family == socket.AF_INET:
                    interfaces[interface].append(f"IPv4: {addr.address} (Netmask: {addr.netmask})")
                elif addr.family == socket.AF_INET6 and not addr.address.startswith('fe80::'):  
                    interfaces[interface].append(f"IPv6: {addr.address}")

    except Exception as e:
        print(f"loi khi lay thong tin giao dien mang: {e}")
    return interfaces

def get_network_stats():
    """Lay thong ke ve luu luong mang"""
    try:
        net_io = psutil.net_io_counters()
        return{
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
        for conn in psutil.net_connections(kind= 'inet'):
            if conn.type == socket.SOCK_STREAM and conn.stats == psutil.CONN_ESTABLISHED:
                process_name = "N/A"
                if conn.pid :
                    try:
                        process = psutil.Process(conn.pid)
                        process_name = process.name()

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_name = "Khong truy cap duoc"
                    except psutil.ZombieProcess:
                        process_name ="Zombie Process"

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

    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        if result == 0:
            try:
                service = socket.getservbyport(port, 'tcp')
            except (OSError, socket.error):
                service = "unknown"
            open_ports.append((port, service))
        sock.close()
    return open_ports

def format_bytes(b):
    """Chuyen doi bytes thanh don vi doc duoc (KB, MB, GB)"""
    if b is None : return 'N/A'
    try:
        b = float(b)
        if b < 0: 
            return "N/A"
            for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']:
                if abs(b) < 1024.0:
                    return f"{b:3.2f} {unit}"
                b /= 1024.0
            return f"{b:.2f} YB"
    except (ValueError, TypeError):
        return "N/A"    