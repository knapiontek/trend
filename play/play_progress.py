import sys
import time

for i in range(100):
    time.sleep(1)
    sys.stdout.write(f'\rcomplete: {i}%%')
    sys.stdout.flush()
