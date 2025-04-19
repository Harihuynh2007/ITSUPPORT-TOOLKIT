import os
import socket
import subprocess
import time
import platform
import re # Them module re de phan tich output ping
from datetime import datetime

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