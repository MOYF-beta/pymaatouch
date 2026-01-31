# pymaatouch

Python wrapper for maatouch (same protocol as minitouch) with the exact API surface as `pyminitouch`.

## Usage

Place `maatouch.apk` in the current working directory (or pass `local_apk_path` explicitly). The library will push it to `/data/local/tmp/maatouch.apk` automatically when connecting.

```python
from pymaatouch import MNTDevice, safe_device, safe_connection, CommandBuilder

DEVICE_ID = "emulator-5554"

# high-level API
with safe_device(DEVICE_ID) as device:
    device.tap([(400, 600)])
    device.swipe([(100, 100), (400, 400), (200, 400)], duration=500)

# low-level API
with safe_connection(DEVICE_ID) as conn:
    builder = CommandBuilder()
    builder.down(0, 400, 400, 50)
    builder.commit()
    builder.up(0)
    builder.commit()
    builder.publish(conn)
```

See [demo.py](demo.py) for a full script mirroring `pyminitouch` examples.

## Differences from minitouch

- Uses `maatouch.apk` and `app_process` (stdin/stdout) instead of socket/port forwarding.
- The touch protocol is identical, so existing command builders and gestures still work.

## Installation

Install dependencies locally, then ensure `maatouch.apk` is available:

```
pip install -e .
# place maatouch.apk next to your script or pass local_apk_path
```

## License

MIT
