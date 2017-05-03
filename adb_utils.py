import subprocess
import random
import time
import sys
import global_params

_TAP_DURATION_MS = 50
MOVE_SWIPE_DURATION_MS = 350

ADB_TIMEOUT_SECONDS = 5


def get_base_cmd_shell():
    return "adb shell" if global_params.device_id is None else "adb -s %s shell" % global_params.device_id


def get_base_cmd_exec():
    return "adb exec-out" if global_params.device_id is None else "adb -s %s exec-out" % global_params.device_id


def tap(x: int, y: int):
    duration = random.randint(_TAP_DURATION_MS, _TAP_DURATION_MS + 100)

    cmd = get_base_cmd_shell() + " input swipe %d %d %d %d %d" % (x, y, x, y, duration)

    while True:
        try:
            subprocess.call(cmd, shell=True, timeout=ADB_TIMEOUT_SECONDS)
            break
        except subprocess.TimeoutExpired:
            print("ADB TIMED OUT!!!! :O :O :O at", time.time(), "- trying again!", file=sys.stderr)


def swipe(from_x, from_y, to_x, to_y):
    duration = random.randint(MOVE_SWIPE_DURATION_MS, MOVE_SWIPE_DURATION_MS + 100)

    cmd = get_base_cmd_shell() + " input swipe %d %d %d %d %d" % (from_x, from_y, to_x, to_y, duration)
    while True:
        try:
            subprocess.call(cmd, shell=True, timeout=ADB_TIMEOUT_SECONDS)
            break
        except subprocess.TimeoutExpired:
            print("ADB TIMED OUT!!!! :O :O :O at", time.time(), "- trying again!", file=sys.stderr)
