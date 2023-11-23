import math
import time
import struct
import sys


duration = float(sys.argv[1])
sys.stdout.write('i am sending floating point values\n')
time.sleep(.5)
date = time.time()

f = open('log.txt', 'w')
while time.time() - date < duration:
    # print('\r', f'{time.time() - date:.04f}', end='')
    f.write(f'{math.sin(time.perf_counter()):.03f} {struct.pack("f", math.sin(time.perf_counter()))}\n')
    sys.stdout.buffer.write(struct.pack('f', math.sin(time.perf_counter())))
    sys.stdout.flush()
    time.sleep(.03)

sys.stdout.write('i stopped sending floating point values\n')
print()
