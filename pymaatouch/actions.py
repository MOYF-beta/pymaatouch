import time
from contextlib import contextmanager

from pymaatouch.logger import logger
from pymaatouch.connection import MNTConnection, MNTServer, safe_connection
from pymaatouch import config
from pymaatouch.utils import restart_adb


class CommandBuilder(object):
    """Build command str for maatouch (same protocol as minitouch)."""

    def __init__(self):
        self._content = ""
        self._delay = 0

    def append(self, new_content):
        self._content += new_content + "\n"

    def commit(self):
        """Add maatouch command: 'c\n'"""
        self.append("c")

    def wait(self, ms):
        """Add maatouch command: 'w <ms>\n'"""
        self.append("w {}".format(ms))
        self._delay += ms

    def up(self, contact_id):
        """Add maatouch command: 'u <contact_id>\n'"""
        self.append("u {}".format(contact_id))

    def down(self, contact_id, x, y, pressure):
        """Add maatouch command: 'd <contact_id> <x> <y> <pressure>\n'"""
        self.append("d {} {} {} {}".format(contact_id, x, y, pressure))

    def move(self, contact_id, x, y, pressure):
        """Add maatouch command: 'm <contact_id> <x> <y> <pressure>\n'"""
        self.append("m {} {} {} {}".format(contact_id, x, y, pressure))

    def publish(self, connection):
        """Apply current commands to your device."""
        self.commit()
        final_content = self._content
        logger.info("send operation: {}".format(final_content.replace("\n", "\\n")))
        connection.send(final_content)
        time.sleep(self._delay / 1000 + config.DEFAULT_DELAY)
        self.reset()

    def reset(self):
        """Clear current commands."""
        self._content = ""
        self._delay = 0


class MNTDevice(object):
    """maatouch device object. API stays compatible with pyminitouch."""

    def __init__(self, device_id, local_apk_path=None):
        self.device_id = device_id
        self.local_apk_path = local_apk_path
        self.server = None
        self.connection = None
        self.start()

    def reset(self):
        self.stop()
        self.start()

    def start(self):
        self.server = MNTServer(self.device_id, local_apk_path=self.local_apk_path)
        self.connection = MNTConnection(self.server)

    def stop(self):
        if self.connection:
            self.connection.disconnect()
        if self.server:
            self.server.stop()

    def tap(self, points, pressure=100, duration=None, no_up=None):
        points = [list(map(int, each_point)) for each_point in points]

        _builder = CommandBuilder()
        for point_id, each_point in enumerate(points):
            x, y = each_point
            _builder.down(point_id, x, y, pressure)
        _builder.commit()

        if duration:
            _builder.wait(duration)
            _builder.commit()

        if not no_up:
            for each_id in range(len(points)):
                _builder.up(each_id)

        _builder.publish(self.connection)

    def swipe(self, points, pressure=100, duration=None, no_down=None, no_up=None):
        points = [list(map(int, each_point)) for each_point in points]

        _builder = CommandBuilder()
        point_id = 0

        if not no_down:
            x, y = points.pop(0)
            _builder.down(point_id, x, y, pressure)
            _builder.publish(self.connection)

        for each_point in points:
            x, y = each_point
            _builder.move(point_id, x, y, pressure)
            if duration:
                _builder.wait(duration)
            _builder.commit()

        _builder.publish(self.connection)

        if not no_up:
            _builder.up(point_id)
            _builder.publish(self.connection)

    def ext_smooth_swipe(
        self, points, pressure=100, duration=None, part=None, no_down=None, no_up=None
    ):
        if not part:
            part = 10

        points = [list(map(int, each_point)) for each_point in points]

        for each_index in range(len(points) - 1):
            cur_point = points[each_index]
            next_point = points[each_index + 1]

            offset = (
                int((next_point[0] - cur_point[0]) / part),
                int((next_point[1] - cur_point[1]) / part),
            )
            new_points = [
                (cur_point[0] + i * offset[0], cur_point[1] + i * offset[1])
                for i in range(part + 1)
            ]
            self.swipe(
                new_points,
                pressure=pressure,
                duration=duration,
                no_down=no_down,
                no_up=no_up,
            )


@contextmanager
def safe_device(device_id, local_apk_path=None):
    """Use MNTDevice safely."""
    _device = MNTDevice(device_id, local_apk_path=local_apk_path)
    try:
        yield _device
    finally:
        time.sleep(config.DEFAULT_DELAY)
        _device.stop()


if __name__ == "__main__":
    restart_adb()

    _DEVICE_ID = "emulator-5554"

    with safe_connection(_DEVICE_ID) as d:
        builder = CommandBuilder()
        builder.down(0, 400, 400, 50)
        builder.commit()
        builder.move(0, 500, 500, 50)
        builder.commit()
        builder.move(0, 800, 400, 50)
        builder.commit()
        builder.up(0)
        builder.commit()
        builder.publish(d)

    with safe_device(_DEVICE_ID) as d:
        builder = CommandBuilder()
        builder.down(0, 400, 400, 50)
        builder.commit()
        builder.move(0, 500, 500, 50)
        builder.commit()
        builder.move(0, 800, 400, 50)
        builder.commit()
        builder.up(0)
        builder.commit()
        builder.publish(d.connection)

    device = MNTDevice(_DEVICE_ID)
    device.tap([(400, 500), (500, 500)], duration=1000)
    time.sleep(1)
    device.stop()

    with safe_device(_DEVICE_ID) as device:
        device.tap([(400, 500), (500, 500)])
        device.swipe([(400, 500), (500, 500)], duration=500)
        time.sleep(0.5)
