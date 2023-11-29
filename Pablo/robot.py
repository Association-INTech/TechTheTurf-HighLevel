import numpy as np
from dataclasses import dataclass
import smbus2
import struct

ENDIANNESS = "<"

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
		kp, ki, kd = struct.unpack(ENDIANNESS+"fff", bys)
		self.set(kp, ki, kd)
		return self

	def to_bytes(self):
		return struct.pack(ENDIANNESS+"fff", self.kp, self.ki, self.kd)

@dataclass
class TelemetryPacketBase:
	timestamp: float

	def fmt():
		return ENDIANNESS+"f"

@dataclass
class PidTelemetryPacket(TelemetryPacketBase):
	target: float
	input: float
	output: float

	def fmt():
		return "fff"

@dataclass
class Telemetry:
	name: str
	idx: int
	packet_type: TelemetryPacketBase
	fmt: str = ""
	size: int = 0

	def __init__(self, name, idx, packet_base):
		self.name = name
		self.idx = idx
		self.packet_type = packet_base
		self.fmt = Telemetry.get_format(packet_base)
		self.size = struct.calcsize(self.fmt)

	def get_format(ty):
		if not "fmt" in ty.__dict__:
			return None
		st = ""
		for base in ty.__bases__:
			if not "fmt" in base.__dict__:
				continue
			st += Telemetry.get_format(base)
		return st + ty.fmt()

	def to_packet(self, data):
		return self.packet_type(*struct.unpack(self.fmt,data))

# Base class with I2C comm helpers

class I2CBase:
	def __init__(self, bus, addr):
		self.bus = bus
		self.addr = addr

	def write(self, reg, data):
		self.bus.write_i2c_block_data(self.addr, reg, data)
		#write = smbus2.i2c_msg.write(addr, struct.pack("<B", reg) + data)
		#bus.i2c_rdwr(write)

	def read(self, reg, size):
		return bytes(self.bus.read_i2c_block_data(self.addr, reg, size))
		#write = smbus2.i2c_msg.write(addr, struct.pack("<B", reg))
		#bus.i2c_rdwr(write)
		#read = smbus2.i2c_msg.read(addr, size)
		#bus.i2c_rdwr(read)
		#return bytes(read)

	def write_struct(self, reg, fmt, *data):
		self.write(reg, struct.pack(ENDIANNESS+fmt, *data))

	def read_struct(self, reg, fmt):
		ret = self.read(reg, struct.calcsize(fmt))
		return struct.unpack(ENDIANNESS+fmt, ret)


# Actual classes for robot functions

class Asserv(I2CBase):
	def __init__(self, bus, addr):
		super().__init__(bus, addr)

		self.last_pos = (0,0) # rho, theta
		self.set_running(False)
		self.pids = {}
		self.telems = {}
		for pid in [Pid("theta", 0), Pid("rho", 1), Pid("left_vel", 2), Pid("right_vel", 3)]:
			self.get_pid(pid)
			idx = pid.idx
			self.pids[idx] = pid
			self.telems[idx] = Telemetry(f"pid_{pid.name}", idx, PidTelemetryPacket)

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

	def telem_from_name(self, name):
		for telem in self.telems.values():
			if telem.name == name:
				return telem
		return None

	def telem_from_idx(self, idx):
		if idx in self.telems:
			return self.telems[idx]
		return None

	# Write registers/ orders

	def set_running(self, state):
		state = not not state
		self.write_struct(0, "B", state)
		self.running = state

	def start(self):
		self.set_running(True)

	def stop(self):
		self.set_running(False)

	def move(self, rho, theta):
		self.write_struct(1, "ff", rho, theta)

	def set_pid(self, pid):
		self.pids[pid.idx] = pid
		self.write(5 | (pid.idx << 4), pid.to_bytes())

	def set_telem(self, telem, state):
		self.write_struct(6 | (telem.idx << 4), "B", state)

	# Read registers

	def get_pos(self):
		self.last_pos = self.read_struct(3, "ff")
		return self.last_pos

	def get_pid(self, pid):
		ret = self.read(2 | (pid.idx << 4), 4*3)
		return pid.from_bytes(ret)

	def get_telem_info(self, telem):
		return self.read_struct(8 | (telem.idx << 4), "II")

	def fetch_telem_single(self, telem):
		dat = self.read(7 | (telem.idx << 4), 4+telem.size)
		rem, = struct.unpack(ENDIANNESS+"I", dat[:4])
		return rem, telem.to_packet(dat[4:])

	def fetch_telem(self, telem, check_avail=True):
		if check_avail:
			rem,_ = self.get_telem_info(telem)
		else:
			rem = 1

		packets = []

		while rem > 0:
			rem, dat = self.fetch_telem_single(telem)
			packets.append(dat)
			print(rem, dat)

		return packets