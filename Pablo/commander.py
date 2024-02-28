import math
import cmd
import time
import robots
import sys

class BaseCommander(cmd.Cmd):
	def __init__(self, pico):
		super(BaseCommander, self).__init__()
		self.pico = pico
		self.started = False

	def do_on(self, arg):
		"""Starts"""
		if self.started:
			print("Déja on")
			return

		self.started = True
		self.pico.start()
		print("ON")

	def do_off(self, arg):
		"""Stops"""
		if not self.started:
			print("Déja off")
			return

		self.started = False
		self.pico.stop()
		print("OFF")

	def do_exit(self, arg):
		"""Stops & quits"""
		print("Ciao")
		self.do_off(arg)
		return True

	def do_telems(self, arg):
		"""list all telemetry"""
		for telem in self.pico.telems.values():
			print(telem)

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
			except Exception:
				print("Pas bon argument")
				return

		if arg[0] == "all":
			for telem in self.pico.telems.values():
				self.pico.set_telem(telem, arg[1])
			return

		try:
			idx = int(arg[0])
			telem = self.pico.telem_from_idx(idx)
		except Exception:
			telem = self.pico.telem_from_name(arg[0])

		if not telem:
			print("Pas bon argument")
			return

		self.pico.set_telem(telem, arg[1])

	def do_ready(self, arg):
		val = self.pico.ready_for_order()
		if val:
			print("Ready")
		else:
			print("Not Ready")


class AsservCommander(BaseCommander):
	def __init__(self, asserv):
		super(AsservCommander, self).__init__(asserv)

	def do_pos(self, arg):
		"""Returns the position of the Asserv Pico"""
		dst,theta = self.pico.get_pos()
		print(f"theta: {math.degrees(theta):.2f}° dst: {dst:.2f}mm")

	def do_move(self, arg):
		"""move (theta) (dst)"""
		if not arg or len(arg.split()) != 2:
			print("Pas de theta et distance")
			return

		if not self.started:
			print("Asserv pas démmaré")
			return

		theta, dst = map(float,arg.split())
		theta = math.radians(theta)

		print(f"Déplacement de theta {theta}rad et rho {dst}")
		self.pico.move(dst, theta)

	def do_pids(self, arg):
		"""list all pids"""
		for pid in self.pico.pids.values():
			print(pid)

	def do_gpid(self, arg):
		"""gpid (id/nom pid)"""
		if not arg:
			print("Pas de numéro/nom de pid")
			return

		try:
			idx = int(arg)
			pid = self.pico.pid_from_idx(idx)
		except Exception:
			pid = self.pico.pid_from_name(arg)

		if not pid:
			print("Pas bon PID")
			return

		self.pico.get_pid(pid)
		print(pid)

	def do_spid(self, arg):
		"""spid (id/nom pid) (kp) (ki) (kd)"""
		arg = arg.split()
		if not arg or len(arg) < 4:
			print("Pas de numéro/nom de pid et valeurs")
			return

		try:
			idx = int(arg[0])
			pid = self.pico.pid_from_idx(idx)
		except Exception:
			pid = self.pico.pid_from_name(arg[0])

		if not pid:
			print("Pas bon PID")
			return

		kp, ki, kd = map(float, arg[1:])
		pid.set(kp, ki, kd)
		print(pid)
		self.pico.set_pid(pid)

	def do_gsp(self, arg):
		"""gets speed profile vmax and amax"""
		vmax, amax = self.pico.get_speedprofile()

		print(f"vmax:{vmax}mm/s amax:{amax}mm/s²")

	def do_ssp(self, arg):
		"""ssp (vmax) (amax)"""
		if not arg or len(arg.split()) != 2:
			print("Pas de vmax et amax")
			return

		vmax, amax = map(float,arg.split())
		self.pico.set_speedprofile(vmax, amax)

	def do_denc(self, arg):
		"""debug cmd: Gets encoder values"""
		left, right = self.pico.debug_get_encoders()

		print(f"Left: {left}, Right: {right}")

	def do_dmot(self, arg):
		"""debug cmd: move (leftval) (rightval)"""
		if not arg or len(arg.split()) != 2:
			print("Pas de vals")
			return

		lval, rval = map(float,arg.split())

		self.pico.debug_set_motors(lval, rval)

	def do_sq(self, arg):
		"""sq (side length)"""
		try:
			side_len = int(arg)
		except Exception:
			print("Pas bon argument")
			return

		self.pico.wait_completed()
		for i in range(4):
			print(i)
			self.pico.move(side_len, 0)
			time.sleep(2)
			self.pico.move(0, math.radians(90))
			time.sleep(2)
			self.pico.wait_completed()


class ActionCommander(BaseCommander):
	def __init__(self, action):
		super(ActionCommander, self).__init__(action)

	def do_demo(self, arg):
		"""debug cmd: demo"""
		self.pico.debug_demo()

	def do_ehomed(self, arg):
		"""Is elevator homed ?"""
		homed = self.pico.elev_homed()
		print("Homed" if homed else "Not Homed")

	def do_epos(self, arg):
		"""Position of elevator (in mm)"""
		pos = self.pico.elev_pos()
		print(f"pos:{pos}mm")

	def do_adeployed(self, arg):
		"""Is arm deployed ?"""
		deployed = self.pico.arm_deployed()
		print("Arm deployed" if deployed else "Arm not deployed (not necessarly folded)")

	def do_ehome(self, arg):
		"""Homes the elevator, needed before moving"""
		self.pico.elev_home()

	def do_emove(self, arg):
		"""emove (pos): absolute position elevator move"""
		try:
			pos = float(arg)
		except Exception:
			print("Pas bon argument")
			return

		self.pico.elev_move_abs(pos)

	def do_emover(self, arg):
		"""emover (pos): relative position elevator move"""
		try:
			pos = float(arg)
		except Exception:
			print("Pas bon argument")
			return

		self.pico.elev_move_rel(pos)

	def do_adeploy(self, arg):
		"""Deploys the arm"""
		self.pico.arm_deploy()

	def do_afold(self, arg):
		"""Folds the arm in compact position"""
		self.pico.arm_fold()

	def do_aturn(self, arg):
		"""aturn: (angle): turn arm head by angle"""
		try:
			angle = float(arg)
		except Exception:
			print("Pas bon argument")
			return

		self.pico.arm_turn(angle)

	def do_pump(self, arg):
		try:
			sp = arg.split(" ")
			idx = int(sp[0])
			state = {"on":True,"off":False}[sp[1]]
		except Exception:
			print("Pas bon argument")
			return

		self.pico.pump_enable(idx, state)


if __name__ == "__main__":
	if len(sys.argv) > 1 and sys.argv[1] == "a":
		commander = ActionCommander(robots.makeAction())
	else:
		commander = AsservCommander(robots.makeAsserv())
	commander.cmdloop()