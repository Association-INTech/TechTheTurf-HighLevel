import math
import cmd
import time
import sys

import comm

def str_to_bool(val):
	val = val.strip().lower()
	if val in ["on", "true", "1"]:
		return True
	elif val in ["off", "false", "0"]:
		return False
	else:
		return None

class BaseCommander(cmd.Cmd):
	def __init__(self, pico):
		super(BaseCommander, self).__init__()
		self.pico = pico
		self.started = False

	def do_on(self, arg):
		"""Starts"""
		if self.started:
			print("Already on")
			return

		self.started = True
		self.pico.start()
		print("ON")

	def do_off(self, arg):
		"""Stops"""
		if not self.started:
			print("Already off")
			return

		self.started = False
		self.pico.stop()
		print("OFF")

	def do_exit(self, arg):
		"""Stops & quits"""
		print("Adios")
		self.do_off(arg)
		return True

	def do_telems(self, arg):
		"""list all telemetry"""
		for telem in self.pico.telems.values():
			print(telem)

	def do_stelem(self, arg):
		"""stelem (idx/name) on/off: turns on or off selected telemetry"""
		arg = arg.strip().lower().split()
		if len(arg) < 2:
			print("Wrong arguments")
			return

		arg[1] = str_to_bool(arg[1])

		if arg[1] is None:
			print("Wrong arguments")
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
			print("Wrong arguments")
			return

		self.pico.set_telem(telem, arg[1])

	def do_ready(self, arg):
		"""ready: checks if the robot is ready to receive a new order"""
		val = self.pico.ready_for_order()
		if val:
			print("Ready")
		else:
			print("Not Ready")

	def do_sb(self, arg):
		"""sb (on/off): enables/disables blocking on commands"""
		arg = str_to_bool(arg)

		if arg is None:
			print("Wrong arguments")
			return

		self.pico.set_blocking(arg)


class AsservCommander(BaseCommander):
	def __init__(self, asserv):
		super(AsservCommander, self).__init__(asserv)

	def do_pos(self, arg):
		"""Returns the position of the Asserv Pico"""
		dst,theta = self.pico.get_pos()
		print(f"theta: {math.degrees(theta):.2f}° dst: {dst:.2f}mm")

	def do_posx(self, arg):
		"""Returns the position of the Asserv Pico in X,Y"""
		x,y = self.pico.get_pos_xy()
		print(f"x,y: {x:.2f}, {y:.2f}mm")

	def do_move(self, arg):
		"""move (theta) (dst)"""
		if not arg or len(arg.split()) != 2:
			print("No thetha and distance")
			return

		if not self.started:
			print("Asserv not started")
			return

		theta, dst = map(float,arg.split())
		theta = math.radians(theta)

		print(f"Moving theta:{theta}rad and rho:{dst}mm")
		self.pico.move(dst, theta)

	def do_pids(self, arg):
		"""list all pids"""
		for pid in self.pico.pids.values():
			print(pid)

	def do_gpid(self, arg):
		"""gpid (id/nom pid)"""
		if not arg:
			print("Wrong arguments")
			return

		try:
			idx = int(arg)
			pid = self.pico.pid_from_idx(idx)
		except Exception:
			pid = self.pico.pid_from_name(arg)

		if not pid:
			print("Wrong PID")
			return

		self.pico.get_pid(pid)
		print(pid)

	def do_spid(self, arg):
		"""spid (id/nom pid) (kp) (ki) (kd)"""
		arg = arg.split()
		if not arg or len(arg) < 4:
			print("Wrong arguments")
			return

		try:
			idx = int(arg[0])
			pid = self.pico.pid_from_idx(idx)
		except Exception:
			pid = self.pico.pid_from_name(arg[0])

		if not pid:
			print("Wrong PID")
			return

		kp, ki, kd = map(float, arg[1:])
		pid.set(kp, ki, kd)
		print(pid)
		self.pico.set_pid(pid)

	def do_gdsp(self, arg):
		"""gets dst speed profile vmax and amax"""
		vmax, amax = self.pico.get_dst_speedprofile()

		print(f"vmax:{vmax}mm/s amax:{amax}mm/s²")

	def do_gasp(self, arg):
		"""gets angle speed profile vmax and amax"""
		vmax, amax = self.pico.get_angle_speedprofile()

		print(f"vmax:{vmax}rad/s amax:{amax}rad/s²")

	def do_sdsp(self, arg):
		"""sdsp (vmax) (amax): sets dst speed profile"""
		if not arg or len(arg.split()) != 2:
			print("No vmax and amax")
			return

		vmax, amax = map(float,arg.split())
		self.pico.set_dst_speedprofile(vmax, amax)

	def do_sasp(self, arg):
		"""sasp (vmax) (amax): sets angle speed profile"""
		if not arg or len(arg.split()) != 2:
			print("No vmax and amax")
			return

		vmax, amax = map(float,arg.split())
		self.pico.set_angle_speedprofile(vmax, amax)

	def do_denc(self, arg):
		"""debug cmd: Gets encoder values"""
		left, right = self.pico.debug_get_encoders()

		print(f"Left: {left}, Right: {right}")

	def do_dmot(self, arg):
		"""debug cmd: dmot (leftval) (rightval)"""
		if not arg or len(arg.split()) != 2:
			print("No left and right values")
			return

		lval, rval = map(float,arg.split())

		self.pico.debug_set_motors(lval, rval)

	def do_dmote(self, arg):
		"""debug cmd: dmote (on/off), enables or disables the motor drivers"""
		arg = str_to_bool(arg)

		if arg is None:
			print("Wrong arguments")
			return

		self.pico.debug_set_motors_enable(arg)

	def do_dstate(self, arg):
		"""debug cmd: dstate, returns the state of the controller"""
		state = self.pico.debug_get_controller_state()
		state = ["Reaching Theta", "Reaching Dst", "Reached target"][state]
		print(f"State: {state}")

	def do_sq(self, arg):
		"""sq (side length)"""
		try:
			side_len = int(arg)
		except Exception:
			print("Wrong arguments")
			return

		for i in range(4):
			print(i)
			self.pico.move(side_len, 0)
			time.sleep(2)
			self.pico.move(0, math.radians(90))
			time.sleep(2)


class ActionCommander(BaseCommander):
	def __init__(self, action):
		super(ActionCommander, self).__init__(action)

	def do_demo(self, arg):
		"""debug cmd: demo"""
		self.pico.start()

		self.pico.pump_enable(0, True)
		print("pe")
		time.sleep(1)
		self.pico.pump_enable(0, False)
		print("pd")

		time.sleep(1)

		self.pico.elev_home()
		print("eh")
		time.sleep(0.5)

		self.pico.elev_move_abs(125)
		print("emove")
		time.sleep(0.5)

		self.pico.elev_move_abs(65)
		print("emove")
		time.sleep(0.5)

		self.pico.elev_move_abs(0)
		print("emove")
		time.sleep(0.5)

		self.pico.elev_home()
		print("eh")

		time.sleep(1)

		self.pico.arm_fold()
		print("af")
		time.sleep(1)

		self.pico.arm_deploy()
		print("ad")
		time.sleep(1)

		self.pico.arm_turn(360)
		print("at")
		time.sleep(0.5)
		self.pico.arm_turn(-180)
		print("at")
		time.sleep(0.5)

		self.pico.arm_fold()
		print("af")

		self.pico.stop()

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

	def do_aangles(self, arg):
		"""Get arm angles, deployed and turn in degrees"""
		dep, turn = self.pico.arm_angles()
		print(f"deploy:{dep}deg, turn:{turn}deg")

	def do_ehome(self, arg):
		"""Homes the elevator, needed before moving"""
		self.pico.elev_home()

	def do_emove(self, arg):
		"""emove (pos): absolute position elevator move"""
		try:
			pos = float(arg)
		except Exception:
			print("Wrong arguments")
			return

		self.pico.elev_move_abs(pos)

	def do_emover(self, arg):
		"""emover (pos): relative position elevator move"""
		try:
			pos = float(arg)
		except Exception:
			print("Wrong arguments")
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
			print("Wrong arguments")
			return

		self.pico.arm_turn(angle)

	def do_pump(self, arg):
		try:
			sp = arg.split(" ")
			idx = int(sp[0])
			state = {"on":True,"off":False}[sp[1]]
		except Exception:
			print("Wrong arguments")
			return

		self.pico.pump_enable(idx, state)


if __name__ == "__main__":
	if len(sys.argv) > 1 and sys.argv[1] == "a":
		commander = ActionCommander(comm.make_action())
	else:
		commander = AsservCommander(comm.make_asserv())
	commander.cmdloop()