import os
import socket
import subprocess
import tempfile

import requests

from pymaatouch import config
from pymaatouch.logger import logger


def str2byte(content):
    """Compile str to byte."""
    return content.encode(config.DEFAULT_CHARSET)


def download_file(target_url):
    """Download file to temp path, and return its file path for further usage."""
    resp = requests.get(target_url)
    resp.raise_for_status()
    temp_path = os.path.join(tempfile.gettempdir(), os.path.basename(target_url))
    with open(temp_path, "wb") as f:
        f.write(resp.content)
    return temp_path


def is_port_using(port_num):
    """Check if port is using by others."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        result = s.connect_ex((config.DEFAULT_HOST, port_num))
        return result == 0
    finally:
        s.close()


def restart_adb():
    """Restart adb server."""
    _ADB = config.ADB_EXECUTOR
    subprocess.check_call([_ADB, "kill-server"])
    subprocess.check_call([_ADB, "start-server"])


def is_device_connected(device_id):
    """Return True if device connected, else return False."""
    _ADB = config.ADB_EXECUTOR
    try:
        device_name = subprocess.check_output(
            [_ADB, "-s", device_id, "shell", "getprop", "ro.product.model"]
        )
        device_name = (
            device_name.decode(config.DEFAULT_CHARSET)
            .replace("\n", "")
            .replace("\r", "")
        )
        logger.info("device {} online".format(device_name))
    except subprocess.CalledProcessError:
        return False
    return True
