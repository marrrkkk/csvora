import time


def poll(fn, timeout_s: float = 20.0, interval_s: float = 0.5):
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        last = fn()
        if last:
            return last
        time.sleep(interval_s)
    return last

