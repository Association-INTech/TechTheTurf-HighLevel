import subprocess
import sys
import time

cmd = 'ssh hindtechno@192.168.1.9 -t'

process = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

while True:
    out = process.stdout.read(1)
    if out == '' and process.poll() != None:
        break
    if out != '':
        sys.stdout.buffer.write(out)
        sys.stdout.flush()