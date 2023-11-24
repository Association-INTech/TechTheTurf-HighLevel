import struct
import subprocess
import sys
import asyncio
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading
import numpy as np
import time

# cmd = 'ssh hindtechno@192.168.1.9 -t'
cmd = 'python just_print_sinus.py 10.'

process = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
)


async def err():
    while process.poll() is None:
        line = await asyncio.to_thread(process.stderr.readline)
        print("ERR", line)


start_check = b'i am sending floating point values\n'
end_check = b'i stopped sending floating point values\n'
checkers = start_check, end_check


grasping_values = False
values = []


def plot():
    while process.poll() is None:
        while not grasping_values and process.poll() is None:
            continue
        while grasping_values and process.poll() is None:
            fig, ax = plt.subplots()
            ax.set_ylim([-1., 1.])
            curve, = ax.plot((), ())
            ax.plot(np.linspace(0, 10., 100), 1 - np.exp(-np.linspace(0, 10., 100)))

            def animate(frame):
                curve.set_data(np.linspace(0, 10., len(values)), values)
                time.sleep(.02)
                return curve,

            ani = FuncAnimation(fig, animate, cache_frame_data=False, blit=True)
            plt.show()


async def out():
    global grasping_values
    # f_total = open('log_buffer.txt', 'w')
    # f = open('log_client.txt', 'w')
    buffer, current_check, float_buffer = b'', start_check, b''
    while process.poll() is None:
        char = await asyncio.to_thread(process.stdout.read, 1)
        if not char:
            continue
        buffer = (buffer + char)[-len(current_check):]
        # f_total.write(str(buffer) + '\n')
        if buffer == current_check:
            grasping_values = not grasping_values
            current_check, values[:], float_buffer = checkers[grasping_values], [], b''
            continue
        if not grasping_values:
            sys.stdout.buffer.write(char)
            sys.stdout.flush()
            continue
        else:
            float_buffer += char
            if len(float_buffer) >= 4:
                values[:] = values[-500:] + [struct.unpack('f', float_buffer[:4])[0]]
                # f.write(f'{values[-1]:.04f} {struct.pack("f", values[-1])} {list(float_buffer[:4])}\n')
                float_buffer = float_buffer[4:]

loop = asyncio.get_event_loop()

threading.Thread(target=plot, daemon=True).start()
loop.run_until_complete(
    asyncio.gather(
        out(),
        err()
    )
)
# threading.Thread(target=loop.run_until_complete, args=(asyncio.gather(
#     out(),
#     err()
# )),)
# plot()
