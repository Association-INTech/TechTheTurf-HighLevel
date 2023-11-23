from multiprocessing import Process, SimpleQueue
from threading import Thread
import asyncio

from controller_classes import ControllerButtons, ControllerMouse, PROCESS, THREAD, ASYNCIO


class ControllerInterface:
    """
    Tool to get events from a ps4 controller, works on UNIX
    """
    
    def __init__(self, queue, joystick_file='/dev/input/js0', mouse_file='/dev/input/mouse0'):
        self.queue = queue
        self.butts, self.mouse = ControllerButtons(queue, joystick_file), ControllerMouse(queue, mouse_file)

    def get_events(self):
        pass

    def start(self):
        pass

    def terminate(self):
        pass


class CProcess(ControllerInterface):
    butt_p, mouse_p = None, None

    def start(self):
        self.butt_p = Process(target=self.butts.mainloop_process)
        self.mouse_p = Process(target=self.mouse.mainloop_process)
        self.butt_p.start()
        self.mouse_p.start()

    def get_events(self):
        while not self.queue.empty():
            yield self.queue.get()

    def terminate(self):
        self.butt_p.terminate()
        self.mouse_p.terminate()


class CThread(ControllerInterface):
    butt_t, mouse_t = None, None

    def start(self):
        self.butt_t = Thread(target=self.butts.mainloop_thread)
        self.mouse_t = Thread(target=self.mouse.mainloop_thread)
        self.butt_t.start()
        self.mouse_t.start()

    def get_events(self):
        while self.queue:
            yield self.queue.pop(0)

    def terminate(self):
        self.butts.running = False
        self.mouse.running = False


class CAsync(ControllerInterface):
    butt_t, mouse_t = None, None

    def get_events(self):
        while self.queue:
            yield self.queue.pop(0)


def async_main():
    controller = CAsync([])

    async def display():
        while True:
            for event in controller.get_events():
                print(event)
            await asyncio.sleep(0.)

    async def main():
        await asyncio.gather(
            display(),
            controller.butts.mainloop_asyncio(),
            controller.mouse.mainloop_asyncio()
        )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        controller.butts.running = False
        controller.mouse.running = False


def process_main():
    controller = CProcess(SimpleQueue())
    controller.start()
    try:
        while True:
            for ev in controller.get_events():
                print(ev)
    except KeyboardInterrupt:
        controller.terminate()


def thread_main():
    controller = CThread([])
    controller.start()
    try:
        while True:
            for ev in controller.get_events():
                print(ev)
    except KeyboardInterrupt:
        controller.terminate()


if __name__ == '__main__':
    import sys
    mode = sys.argv[1]
    {'asyncio': async_main, 'thread': thread_main, 'process': process_main}[mode]()
