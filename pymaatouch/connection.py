import os
import select
import subprocess
from contextlib import contextmanager

from .logger import logger
from . import config
from .utils import is_device_connected

_ADB = config.ADB_EXECUTOR


class MAAInstaller(object):
    """Install maatouch apk to device if missing."""

    def __init__(self, device_id, local_apk_path=None):
        self.device_id = device_id
        self.local_apk_path = local_apk_path or config.MAA_LOCAL_APK

    def ensure_installed(self):
        if self._is_installed():
            logger.info("maatouch already installed on {}".format(self.device_id))
            return
        self._push_apk()

    def _is_installed(self):
        try:
            file_list = subprocess.check_output(
                [_ADB, "-s", self.device_id, "shell", "ls", os.path.dirname(config.MAA_REMOTE_PATH)]
            )
        except subprocess.CalledProcessError:
            return False
        return os.path.basename(config.MAA_REMOTE_PATH) in file_list.decode(config.DEFAULT_CHARSET)

    def _push_apk(self):
        if not os.path.exists(self.local_apk_path):
            raise FileNotFoundError(
                "Local maatouch apk not found: {}".format(self.local_apk_path)
            )
        logger.info(
            "pushing {} to {}".format(self.local_apk_path, config.MAA_REMOTE_PATH)
        )
        subprocess.check_call(
            [_ADB, "-s", self.device_id, "push", self.local_apk_path, config.MAA_REMOTE_PATH]
        )
        subprocess.check_call(
            [_ADB, "-s", self.device_id, "shell", "chmod", "644", config.MAA_REMOTE_PATH]
        )
        logger.info("maatouch installed for {}".format(self.device_id))


class MNTServer(object):
    """
    Manage maatouch process. Different from minitouch: we talk via adb shell stdin/stdout.
    """

    def __init__(self, device_id, local_apk_path=None):
        assert is_device_connected(device_id)
        self.device_id = device_id
        self.local_apk_path = local_apk_path
        self.installer = MAAInstaller(device_id, local_apk_path)
        self.installer.ensure_installed()

        self.process = None
        self.header_lines = []
        self.max_contacts = None
        self.max_x = None
        self.max_y = None
        self.max_pressure = None
        self.pid = None

        self._start_maa()

    def _start_maa(self):
        command_list = [
            _ADB,
            "-s",
            self.device_id,
            "shell",
            config.MAA_START_CMD,
        ]
        logger.info("start maatouch: {}".format(" ".join(command_list)))
        self.process = subprocess.Popen(
            command_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._read_header()

    def _read_header(self):
        # maatouch sometimes prints header slowly; avoid blocking forever
        fd = self.process.stdout.fileno()
        for _ in range(config.HEADER_MAX_LINES):
            ready, _, _ = select.select([fd], [], [], 3)
            if not ready:
                logger.warning("waiting header timed out; continuing")
                break
            line = self.process.stdout.readline()
            if not line:
                break
            line = line.strip()
            self.header_lines.append(line)
            if line.startswith("^"):
                parts = line.split(" ")
                if len(parts) >= 5:
                    _, max_contacts, max_x, max_y, max_pressure = parts[:5]
                    self.max_contacts = max_contacts
                    self.max_x = max_x
                    self.max_y = max_y
                    self.max_pressure = max_pressure
            if line.startswith("$"):
                parts = line.split(" ")
                if len(parts) >= 2:
                    self.pid = parts[1]
        logger.info("maatouch header: {}".format(" | ".join(self.header_lines)))

    def heartbeat(self):
        return self.process and self.process.poll() is None

    def stop(self):
        if self.process:
            self.process.kill()
            try:
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.stderr.close()
            except Exception:
                pass
            logger.info("maatouch stopped for {}".format(self.device_id))


class MNTConnection(object):
    """Manage stdin/stdout pipe to maatouch process."""

    _DEFAULT_HOST = config.DEFAULT_HOST
    _DEFAULT_BUFFER_SIZE = config.DEFAULT_BUFFER_SIZE

    def __init__(self, server):
        self.server = server
        self.process = server.process
        self.max_contacts = server.max_contacts
        self.max_x = server.max_x
        self.max_y = server.max_y
        self.max_pressure = server.max_pressure
        self.pid = server.pid

    def disconnect(self):
        if self.process:
            try:
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.stderr.close()
            except Exception:
                pass
            logger.info("maatouch disconnected")
        self.process = None

    def send(self, content):
        """Send message to maatouch."""
        if not self.process:
            raise RuntimeError("maatouch process already closed")
        if not content.endswith("\n"):
            content += "\n"
        self.process.stdin.write(content)
        self.process.stdin.flush()
        # maatouch does not echo responses by default
        return None


@contextmanager
def safe_connection(device_id, local_apk_path=None):
    """Safe connection runtime to use."""

    server = MNTServer(device_id, local_apk_path=local_apk_path)
    connection = MNTConnection(server)
    try:
        yield connection
    finally:
        connection.disconnect()
        server.stop()
