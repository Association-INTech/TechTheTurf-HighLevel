import subprocess
import sys
import asyncio

cmd = 'ssh hindtechno@192.168.1.9 -t'

process = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)


async def err():
    while process.poll() is None:
        line = await asyncio.to_thread(process.stderr.readline)
        print("ERR", line)


start_check = 'i am sending floating point values\r\n'.encode()
end_check = 'i stopped sending floating point values\r\n'.encode()
checkers = start_check, end_check


async def out():
    f = open('log.txt', 'w')
    buffer, current_check, grasping_values = b'', start_check, False
    while process.poll() is None:
        char = await asyncio.to_thread(process.stdout.read, 1)
        if not char:
            continue
        buffer = (buffer + char)[-len(current_check):]
        f.write(str(buffer) + '\n')
        if buffer == current_check:
            grasping_values = not grasping_values
            print(f'{grasping_values = }')
            current_check = checkers[grasping_values]
        if not grasping_values:
            sys.stdout.buffer.write(char)
            sys.stdout.flush()
            continue

loop = asyncio.get_event_loop()

loop.run_until_complete(
    asyncio.gather(
        out(),
        err()
    )
)

