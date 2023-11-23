import math
import time
import struct
import sys


duration, date = float(sys.argv[1]), time.perf_counter()

while time.perf_counter() - date < duration:
    print('\r', time.perf_counter() - date, end='')
    # sys.stdout.buffer.write(struct.pack('f', math.sin(time.perf_counter() / 1e6)))
    # sys.stdout.flush()