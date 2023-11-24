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
    val = math.sin(time.perf_counter())
    f.write(f'{val:.03f} {struct.pack("f", val)} {list(struct.pack("f", val))}\n')
    sys.stdout.buffer.write(struct.pack('f', val))
    time.sleep(.3)

sys.stdout.write('i stopped sending floating point values\n')
print()
