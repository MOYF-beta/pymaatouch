import platform

# connection
DEFAULT_HOST = "127.0.0.1"
DEFAULT_BUFFER_SIZE = 0
DEFAULT_CHARSET = "utf-8"

# operation
DEFAULT_DELAY = 0.05

# installer
MAA_REMOTE_PATH = "/data/local/tmp/maatouch.apk"
# default local name matches the provided binary in repo
MAA_LOCAL_APK = "maatouch"
MAA_START_CMD = (
    f"export CLASSPATH={MAA_REMOTE_PATH}; app_process /data/local/tmp com.shxyke.MaaTouch.App"
)
HEADER_MAX_LINES = 3

# system
SYSTEM_NAME = platform.system()
NEED_SHELL = SYSTEM_NAME != "Windows"
ADB_EXECUTOR = "adb"
