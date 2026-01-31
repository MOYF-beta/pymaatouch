from pymaatouch import safe_connection, safe_device, MNTDevice, CommandBuilder

_DEVICE_ID = "emulator-5554"

# The maatouch apk should be placed locally as 'maatouch.apk' (or pass local_apk_path=...).

# ---

device = MNTDevice(_DEVICE_ID)

print("max x: ", device.connection.max_x)
print("max y: ", device.connection.max_y)

# single-tap
device.tap([(400, 600)])
# multi-tap
device.tap([(400, 400), (600, 600)])
# set the pressure, default == 100
device.tap([(400, 600)], pressure=50)

# long-time-tap
device.tap([(400, 600)], duration=2000)

device.tap([(400, 600)], duration=2000, no_up=True)

# swipe
device.swipe([(100, 100), (500, 500)])
device.swipe([(100, 100), (400, 400), (200, 400)], duration=500, pressure=50)

# continue actions
device.tap([(400, 600)], duration=2000, no_up=True)
device.swipe(
    [(400, 600), (400, 400), (200, 400)],
    duration=500,
    pressure=50,
    no_down=True,
    no_up=True,
)
device.swipe(
    [(200, 400), (400, 400), (400, 600)], duration=500, pressure=50, no_down=True
)

device.ext_smooth_swipe(
    [(100, 100), (400, 400), (200, 400)], duration=500, pressure=50, part=20
)

device.stop()

# ---

with safe_device(_DEVICE_ID) as device:
    device.tap([(400, 600)])
    device.tap([(400, 400), (600, 600)])
    device.tap([(400, 600)], pressure=50)

# ---

with safe_connection(_DEVICE_ID) as connection:
    builder = CommandBuilder()
    builder.down(0, 400, 400, 50)
    builder.commit()
    builder.move(0, 500, 500, 50)
    builder.commit()
    builder.move(0, 800, 400, 50)
    builder.commit()
    builder.up(0)
    builder.commit()

    builder.publish(connection)

_OPERATION = """
d 0 150 150 50\n
c\n
u 0\n
c\n
"""

with safe_connection(_DEVICE_ID) as conn:
    conn.send(_OPERATION)
