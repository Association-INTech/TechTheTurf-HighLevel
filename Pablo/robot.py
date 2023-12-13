import numpy as np
from dataclasses import dataclass
import struct
import time

import telemetry

ENDIANNESS = "<"
POLLING_RATE = 50

@dataclass
class Pid:
	name: str
	idx: int
	kp: float = 0
	ki: float = 0
	kd: float = 0

	def set(self, kp, ki, kd):
		self.kp = kp
		self.ki = ki
		self.kd = kd
		return self

	def from_bytes(self, bys):
		kp, ki, kd = struct.unpack(ENDIANNESS + "fff", bys)
		self.set(kp, ki, kd)
		return self

	def to_bytes(self):
		return struct.pack(ENDIANNESS + "fff", self.kp, self.ki, self.kd)

# Base class with I2C comm helpers

class I2CBase:
	def __init__(self, bus=None, addr=None):
		self.bus = bus
		self.addr = addr
		self.i2cSimulate = bus is None

	def write(self, reg, data):
		if self.i2cSimulate:
			return
		self.bus.write_i2c_block_data(self.addr, reg, data)

	def read(self, reg, size):
		if self.i2cSimulate:
			return b"\x00"*size
		return bytes(self.bus.read_i2c_block_data(self.addr, reg, size))

	def write_struct(self, reg, fmt, *data):
		self.write(reg, struct.pack(ENDIANNESS + fmt, *data))

	def read_struct(self, reg, fmt):
		ret = self.read(reg, struct.calcsize(fmt))
		return struct.unpack(ENDIANNESS + fmt, ret)

# Base class for pico microcontrollers on robots

class PicoBase(I2CBase):
	def __init__(self, bus=None, addr=None):
		super().__init__(bus, addr)
		self.set_running(False)
		self.telems = {}

	# Data helpers

	def telem_from_name(self, name):
		for telem in self.telems.values():
			if telem.name == name:
				return telem
		return None

	def telem_from_idx(self, idx):
		if idx in self.telems:
			return self.telems[idx]
		return None

	# Writer registers/ orders

	def set_running(self, state):
		state = not not state
		self.write_struct(0, "B", state)
		self.running = state

	def start(self):
		self.set_running(True)

	def stop(self):
		self.set_running(False)

	def set_telem(self, telem, state):
		self.write_struct(6 | (telem.idx << 4), "B", state)

	# Read registers

	def ready_for_order(self):
		return self.read_struct(10, "B")[0] == 1

	# Command Helpers

	def wait_completed(self):
		while not self.ready_for_order():
			time.sleep(1.0/POLLING_RATE)

# Class for the pico that handles moving

class Asserv(PicoBase):
	def __init__(self, bus=None, addr=None):
		super().__init__(bus, addr)

		self.last_pos = (0,0) # rho, theta
		self.set_running(False)
		self.pids = {}
		for pid in [Pid("theta", 0), Pid("rho", 1), Pid("left_vel", 2), Pid("right_vel", 3)]:
			self.get_pid(pid)
			idx = pid.idx
			self.pids[idx] = pid
			self.telems[idx] = telemetry.Telemetry(f"pid_{pid.name}", idx, telemetry.PidTelemetryPacket)

		for telem in self.telems.values():
			self.set_telem(telem, False)

	# Data helpers

	def pid_from_name(self, name):
		for pid in self.pids.values():
			if pid.name == name:
				return pid
		return None

	def pid_from_idx(self, idx):
		if idx in self.pids:
			return self.pids[idx]
		return None

	# Write registers/ orders

	def move(self, rho, theta):
		self.write_struct(1, "ff", rho, theta)

	def set_pid(self, pid):
		self.pids[pid.idx] = pid
		self.write(5 | (pid.idx << 4), pid.to_bytes())

	# Read registers

	def get_pos(self):
		self.last_pos = self.read_struct(3, "ff")
		return self.last_pos

	def get_pid(self, pid):
		ret = self.read(2 | (pid.idx << 4), 4*3)
		return pid.from_bytes(ret)