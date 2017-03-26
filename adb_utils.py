import subprocess
import random

_TAP_DURATION_MS = 200
MOVE_SWIPE_DURATION_MS = 350

ADB_TIMEOUT_SECONDS = 5


def tap(x: int, y: int):
    duration = random.randint(_TAP_DURATION_MS, _TAP_DURATION_MS + 100)
    subprocess.call("adb shell input swipe %d %d %d %d %d" % (x, y, x, y, duration), shell=True,
                    timeout=ADB_TIMEOUT_SECONDS)


def swipe(from_x, from_y, to_x, to_y):
    duration = random.randint(MOVE_SWIPE_DURATION_MS, MOVE_SWIPE_DURATION_MS + 100)
    subprocess.call("adb shell input swipe %d %d %d %d %d" % (from_x, from_y, to_x, to_y, duration), shell=True,
                    timeout=ADB_TIMEOUT_SECONDS)
