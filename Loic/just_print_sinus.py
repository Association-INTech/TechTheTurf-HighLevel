import math
import time
import struct
import sys


duration = float(sys.argv[1])
sys.stdout.buffer.write(b'i am sending floating point values')
sys.stdout.flush()
time.sleep(.5)
date = time.time()

f = open('log_server.txt', 'w')
while time.time() - date < duration:
    # print('\r', f'{time.time() - date:.04f}', end='')
    val = math.sin(time.perf_counter())
    f.write(f'{val:.03f} {struct.pack("f", val)} {list(struct.pack("f", val))}\n')
    sys.stdout.buffer.write(struct.pack('f', val))
    time.sleep(.03)
    sys.stdout.flush()


sys.stdout.buffer.write(b'i stopped sending floating point values')
sys.stdout.flush()
print()
