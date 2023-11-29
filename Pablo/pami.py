import numpy as np
import math
import cmd
import smbus2
import robot

PAMI_I2C_ADDR = 0x69

class Commander(cmd.Cmd):
	def __init__(self, asserv):
		super(Commander, self).__init__()
		self.asserv = asserv
		self.started = False

	def do_on(self, arg):
		"""Starts"""
		if self.started:
			print("Pami déja on")
			return

		self.started = True
		self.asserv.start()
		print("Pami - ON")

	def do_off(self, arg):
		"""Stops"""
		if not self.started:
			print("Pami déja off")
			return

		self.started = False
		self.asserv.stop()
		print("Pami - OFF")

	def do_exit(self, arg):
		"""Stops & quits"""
		print("Ciao")
		self.do_off(arg)
		return True

	def do_pos(self, arg):
		"""Returns the position of the Pami"""
		dst,theta = self.asserv.get_pos()
		print(f"theta: {theta}rad, dst:{dst}")

	def do_move(self, arg):
		"""move (theta) (dst)"""
		if not arg or len(arg.split()) != 2:
			print("Pas de theta et distance")
			return

		if not self.started:
			print("Pami pas démmaré")
			return

		theta, dst = map(float,arg.split())
		theta = math.radians(theta)

		print(f"Déplacement de theta {theta}rad et rho {dst}")
		self.asserv.move(dst, theta)

	def do_gpid(self, arg):
		"""gpid (id/nom pid)"""
		if not arg:
			print("Pas de numéro/nom de pid")
			return

		try:
			idx = int(arg)
			pid = self.asserv.pid_from_idx(idx)
		except:
			pid = self.asserv.pid_from_name(arg)

		if not pid:
			print("Pas bon PID")
			return

		self.asserv.get_pid(pid)
		print(pid)

	def do_spid(self, arg):
		"""spid (id/nom pid) (kp) (ki) (kd)"""
		arg = arg.split()
		if not arg or len(arg) < 4:
			print("Pas de numéro/nom de pid et valeurs")
			return

		try:
			idx = int(arg[0])
			pid = self.asserv.pid_from_idx(idx)
		except:
			pid = self.asserv.pid_from_name(arg[0])

		if not pid:
			print("Pas bon PID")
			return

		kp, ki, kd = map(float, arg[1:])
		pid.set(kp, ki, kd)
		print(pid)
		self.asserv.set_pid(pid)

	def do_stelem(self, arg):
		"""stelem (idx/name) on/off """
		arg = arg.strip().lower().split()
		if len(arg) < 2:
			print("Pas bon argument")
			return
		if arg[1] == "on":
			arg[1] = True
		elif arg[1] == "off":
			arg[1] = False
		else:
			try:
				arg[1] = bool(arg[1])
			except:
				print("Pas bon argument")
				return

		try:
			idx = int(arg[0])
			telem = self.asserv.telem_from_idx(idx)
		except:
			telem = self.asserv.telem_from_name(idx)

		if not telem:
			print("Pas bon argument")
			return

		self.asserv.set_telem(telem, arg[1])

	def do_telem(self, arg):
		"""telem (id)"""
		try:
			idx = int(arg[0])
			telem = self.asserv.telem_from_idx(idx)
		except:
			telem = self.asserv.telem_from_name(idx)

		if not telem:
			print("Pas bon argument")
			return

		self.asserv.fetch_telem(telem)

if __name__ == "__main__":
	bus = smbus2.SMBus(1)
	asserv = robot.Asserv(bus, PAMI_I2C_ADDR)
	
	cmd_handler = Commander(asserv)
	cmd_handler.cmdloop()