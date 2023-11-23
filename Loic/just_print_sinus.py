import math
import time
import struct
import sys


while True:
    sys.stdout.buffer.write(struct.pack('f', math.sin(time.perf_counter() / 1e6)))
    sys.stdout.flush()