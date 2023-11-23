import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from matplotlib.animation import FuncAnimation
import cmd
import smbus2
import struct

bus = smbus2.SMBus(1)
PAMI_I2C_ADDR = 0x69  # normalement 0x69

@dataclass
class Pid:
	name: str
	kp: float = 0
	ki: float = 0
	kd: float = 0

	def set(self, kp, ki, kd):
		self.kp = kp
		self.ki = ki
		self.kd = kd

	def from_bytes(self, bys):
		kp, ki, kd = struct.unpack("<fff", bys)
		self.set(kp, ki, kp)

	def to_bytes(self):
		return struct.pack("<fff", self.kp, self.ki, self.kd)

	def __str__(self):
		return f"Pid(name={self.name}, kp={self.kp}, ki={self.ki}, kd={self.kd})"

def write_i2c(bus, addr, reg, data):
	#write = smbus2.i2c_msg.write(addr, struct.pack("<B", reg) + data)
	#bus.i2c_rdwr(write)
	bus.write_i2c_block_data(addr, reg, data)

def read_i2c(bus, addr, reg, size):
	return bytes(bus.read_i2c_block_data(addr, reg, size))
	#write = smbus2.i2c_msg.write(addr, struct.pack("<B", reg))
	#bus.i2c_rdwr(write)
	#read = smbus2.i2c_msg.read(addr, size)
	#bus.i2c_rdwr(read)
	#return bytes(read)

class Pami(cmd.Cmd):
	def __init__(self, addr):
		super(Pami, self).__init__()
		self.addr = addr
		self.started = False

		self.pids = [Pid("theta"), Pid("rho"), Pid("left_vel"), Pid("right_vel")]

	def do_on(self, arg):
		"""Allume le Pami"""
		write_i2c(bus, self.addr, 0, struct.pack('<B', 1))

		self.started = True
		print("Pami - ON")

	def do_off(self, arg):
		"""éteint le pami, le stoppe et remet ses roues droites"""
		write_i2c(bus, self.addr, 0, struct.pack('<B', 0))

		self.started = False
		print("Pami - OFF")

	def do_exit(self, arg):
		"""stoppe le moteur, eteint le pami et ferme le terminal"""
		print("Ciao")
		self.do_off()
		return True

	def do_pos(self, arg):
		"""demande la position et l'angle teta d'orientation du robot"""
		res = read_i2c(bus, self.addr, 3, 2*4)
		theta,dst = struct.unpack("<ff", res)
		print(f"theta: {theta}, dst:{dst}")

	def do_move(self, arg):
		"""Déplacement de theta + distance"""
		if not arg:
			print("Pas de theta et distance")
			return

		if not self.started:
			print("Pami pas démmaré")
			return

		theta, dst = map(float,arg.split())

		write_i2c(bus, self.addr, 1, struct.pack('<ff', dst, theta))
		print(f"Déplacement de theta {theta} et rho {dst}")

	def do_gpid(self, arg):
		"""Demandes les valeurs du PID spécifié"""
		if not arg:
			print("Pas de numéro/nom de pid")
			return

		try:
			idx = int(arg)
		except:
			found = False
			for idx,p in enumerate(self.pids):
				if p.name == arg:
					found = True
					break
			if not found:
				print("Pas bon Pid")
				return

		res = read_i2c(bus, self.addr, 2 | (idx << 4), 4*3)
		self.pids[idx].from_bytes(res)
		print(self.pids[idx])

	def do_spid(self, arg):
		"""Change les valeurs du PID spécifié"""
		arg = arg.split()
		if not arg or len(arg) < 4:
			print("Pas de numéro/nom de pid et valeurs")
			return

		try:
			idx = int(arg[0])
		except:
			found = False
			for idx,p in enumerate(self.pids):
				if p.name == arg[0]:
					found = True
					break
			if not found:
				print("Pas bon Pid")
				return

		kp, ki, kd = map(float, arg[1:])
		self.pids[idx].set(kp, ki, kd)
		print(self.pids[idx])
		write_i2c(bus, self.addr, 5 | (idx << 4), self.pids[idx].to_bytes())

if __name__ == "__main__":
	pami = Pami(PAMI_I2C_ADDR)
	pami.cmdloop()