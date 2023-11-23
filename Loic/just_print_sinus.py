import math
import time
import struct
import sys


sys.stderr.write('i am sending floating point values\n')
time.sleep(.5)
duration, date = float(sys.argv[1]), time.time()

while time.time() - date < duration:
    print('\r', f'{time.time() - date:.04f}', end='')
    # sys.stdout.buffer.write(struct.pack('f', math.sin(time.perf_counter() / 1e6)))
    # sys.stdout.flush()
    time.sleep(.03)

sys.stderr.write('i stopped sending floating point values\n')

print()