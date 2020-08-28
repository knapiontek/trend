import sys
import time


def progress(i: int, max: int):
    sys.stdout.write(f'\rcomplete: {100 * i / max:.1f}%')
    sys.stdout.flush()


for i in range(134):
    time.sleep(0.3)
    progress(i, 133)
