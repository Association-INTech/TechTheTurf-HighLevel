import subprocess
import sys
import asyncio

cmd = 'ssh hindtechno@192.168.1.9 -t'

process = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)


async def err():
    while process.poll() is None:
        print('err coince')
        line = await asyncio.to_thread(process.stderr.readline)
        print("ERR", line)


async def out():

    while process.poll() is None:
        char = await asyncio.to_thread(process.stdout.read, 1)
        if char:
            sys.stdout.buffer.write(char)
            sys.stdout.flush()

loop = asyncio.get_event_loop()

loop.run_until_complete(
    asyncio.gather(
        out(),
        err()
    )
)

while process.poll():
    pass
