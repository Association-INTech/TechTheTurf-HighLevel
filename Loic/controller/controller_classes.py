import struct
from constants import *
import asyncio


class Event:
    # fixes the attributes
    __slots__ = 'button', 'type', 'value'

    def __init__(self, button, type_, value):
        self.button, self.type, self.value = button, 0 if type_ < 0 else type_, value

    def __repr__(self):
        return EVENT_FORMAT.format(EVENT_TYPES[self.type], BUTTONS.get((self.type, self.button), ""), self.value)


class ControllerInterface:
    event_length: int
    running = True

    def read_process_thread(self, file):
        return file.read(self.event_length)

    async def read_asyncio(self, file):
        return await asyncio.to_thread(file.read, self.event_length)


class ControllerButtons(ControllerInterface):
    event_format = '3Bh2b'
    event_length = struct.calcsize(event_format)

    def __init__(self, queue, location):
        self.file, self.queue = location, queue

    def mainloop_process(self):
        try:
            with open(self.file, 'rb') as f:
                while True:
                    # read will block, that's why i use processes
                    self.queue.put(Event(*struct.unpack(self.event_format, self.read_process_thread(f)[:2:-1])))
        except KeyboardInterrupt:
            print('Terminated Controller Process')
        except OSError:
            print('Controller Disconnected')

    async def mainloop_asyncio(self):
        try:
            with open(self.file, 'rb') as f:
                while self.running:
                    self.queue.append(Event(*struct.unpack(
                        self.event_format, (await self.read_asyncio(f))[:2:-1]
                    )))
        except KeyboardInterrupt:
            print('Terminated Controller Process')
        except OSError:
            print('Controller Disconnected')

    def mainloop_thread(self):
        try:
            with open(self.file, 'rb') as f:
                while self.running:
                    self.queue.append(Event(*struct.unpack(
                        self.event_format, self.read_process_thread(f)[:2:-1]
                    )))
        except KeyboardInterrupt:
            print('Terminated Controller Process')
        except OSError:
            print('Controller Disconnected')


class ControllerMouse(ControllerInterface):
    event_length = 3

    def __init__(self, queue, location):
        self.file, self.queue = location, queue
        self.pad_state = 0

    def mainloop_process(self):
        try:
            with open(self.file, 'rb') as f:
                while True:
                    # will block, that's why i use processes
                    h, dx, dy = self.read_process_thread(f)
                    if (h & 1) ^ self.pad_state:
                        self.pad_state = h & 1
                        self.queue.put(Event(h & 1, 3, None))
                    # Two's complement on x and y displacements
                    self.queue.put(Event(h & 1, 3, ((dx - 256 if dx > 128 else dx), dy - 256 if dy > 128 else dy)))
        except KeyboardInterrupt:
            print('Terminated Mouse Process')
        except OSError:
            print('Controller Disconnected')

    def mainloop_thread(self):
        try:
            with open(self.file, 'rb') as f:
                while self.running:
                    # will block, that's why i use processes
                    h, dx, dy = self.read_process_thread(f)
                    if (h & 1) ^ self.pad_state:
                        self.pad_state = h & 1
                        self.queue.append(Event(h & 1, 3, None))
                    # Two's complement on x and y displacements
                    self.queue.append(Event(h & 1, 3, ((dx - 256 if dx > 128 else dx), dy - 256 if dy > 128 else dy)))
        except KeyboardInterrupt:
            print('Terminated Mouse Process')
        except OSError:
            print('Controller Disconnected')

    async def mainloop_asyncio(self):
        try:
            with open(self.file, 'rb') as f:
                while self.running:
                    # will block, that's why i use processes
                    h, dx, dy = await self.read_asyncio(f)
                    if (h & 1) ^ self.pad_state:
                        self.pad_state = h & 1
                        self.queue.append(Event(h & 1, 3, None))
                    # Two's complement on x and y displacements
                    self.queue.append(Event(h & 1, 3, ((dx - 256 if dx > 128 else dx), dy - 256 if dy > 128 else dy)))
        except KeyboardInterrupt:
            print('Terminated Mouse Process')
        except OSError:
            print('Controller Disconnected')