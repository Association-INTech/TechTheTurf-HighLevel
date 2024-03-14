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

	def write_cmd(self, reg):
		self.write(reg, [])

	def write_struct(self, reg, fmt, *data):
		self.write(reg, struct.pack(ENDIANNESS + fmt, *data))

	def read_struct(self, reg, fmt):
		ret = self.read(reg, struct.calcsize(fmt))
		return struct.unpack(ENDIANNESS + fmt, ret)

# A decorator to block until the command has finished
def block_cmd(func):

	def inner(self, *args, **kwargs):
		# Call the function normally
		func(self, *args, **kwargs)

		# If we need to block, do so
		if self.is_blocking():
			self.wait_completed()

	return inner


# Base class for pico microcontrollers on robots

class PicoBase(I2CBase):
	def __init__(self, bus=None, addr=None):
		super().__init__(bus, addr)
		self.set_blocking(True)
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

	# Blocking state logic

	def set_blocking(self, val):
		self.blocking = val

	def is_blocking(self):
		return self.blocking

	# Writer registers/ orders

	@block_cmd
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
		self.last_pos_xy = (0,0) # x, y
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

	@block_cmd
	def move(self, rho, theta):
		self.write_struct(1, "ff", rho, theta)

	def set_pid(self, pid):
		self.pids[pid.idx] = pid
		self.write(5 | (pid.idx << 4), pid.to_bytes())

	def set_speedprofile(self, vmax, amax):
		return self.write_struct(13 | (0 << 4), "ff", vmax, amax)

	# Read registers

	def get_pos(self):
		self.last_pos = self.read_struct(3 | (0 << 4), "ff")
		return self.last_pos

	def get_pos_xy(self):
		self.last_pos_xy = self.read_struct(3 | (1 << 4), "ff")
		return self.last_pos_xy

	def get_pid(self, pid):
		ret = self.read(2 | (pid.idx << 4), 4*3)
		return pid.from_bytes(ret)

	def get_speedprofile(self):
		return self.read_struct(12 | (0 << 4), "ff")

	# Read/Write

	# returns left,right ticks
	def debug_get_encoders(self):
		return self.read_struct(11 | (0 << 4), "ii")

	# sets motor speed values manually
	def debug_set_motors(self, left, right):
		self.write_struct(11 | (1 << 4), "ff", left, right)

	def debug_set_target(self, dst, theta):
		self.write_struct(11 | (2 << 4), "ff", dst, theta)

# Class for the pico that handles actuators

class Action(PicoBase):
	def __init__(self, bus=None, addr=None):
		super().__init__(bus, addr)

	# Read

	def elev_homed(self):
		return self.read_struct(1 | (3 << 4), "?")[0]

	def elev_pos(self):
		return self.read_struct(1 | (4 << 4), "f")[0]

	def arm_deployed(self):
		return self.read_struct(2 | (3 << 4), "?")[0]

	def arm_angles(self):
		return self.read_struct(2 | (4 << 4), "ff")

	# Write

	@block_cmd
	def elev_home(self):
		self.write_cmd(1 | (0 << 4))

	@block_cmd
	def elev_move_abs(self, pos):
		self.write_struct(1 | (1 << 4), "f", pos)

	@block_cmd
	def elev_move_rel(self, pos):
		self.write_struct(1 | (2 << 4), "f", pos)

	@block_cmd
	def arm_deploy(self):
		self.write_cmd(2 | (0 << 4))

	@block_cmd
	def arm_fold(self):
		self.write_cmd(2 | (1 << 4))

	@block_cmd
	def arm_turn(self, angle):
		self.write_struct(2 | (2 << 4), "f", angle)

	@block_cmd
	def pump_enable(self, pump_idx, state):
		self.write_struct(3 | (pump_idx << 4), "?", state)

	# Read/Write

	#def debug_demo(self):
	#	self.write_cmd(15)