import math
import time
import argparse
import cmd2

import enum
import comm
try:
	import handlers
except Exception as e:
	print(f"Couldn't import handlers, continuing ({e})")


def str2bool(v):
	if isinstance(v, bool):
		return v
	if v.lower() in {'on', 'yes', 'true', 't', 'y', '1'}:
		return True
	elif v.lower() in {'off', 'no', 'false', 'f', 'n', '0'}:
		return False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')

def hex2int(v):
	return int(v, 16)

class EnumAction(argparse.Action):
	"""
	Argparse action for handling Enums
	"""
	def __init__(self, **kwargs):
		# Pop off the type value
		enum_type = kwargs.pop("type", None)

		# Ensure an Enum subclass is provided
		if enum_type is None:
			raise ValueError("type must be assigned an Enum when using EnumAction")
		if not issubclass(enum_type, enum.Enum):
			raise TypeError("type must be an Enum when using EnumAction")

		# Generate choices from the Enum
		kwargs.setdefault("choices", tuple(e.name.lower() for e in enum_type))

		super(EnumAction, self).__init__(**kwargs)

		self._enum = enum_type

	def __call__(self, parser, namespace, values, option_string=None):
		# Convert value back into an Enum
		value = None
		for val in self._enum:
			if val.name.lower() == values:
				value = val
		if value is None:
			raise argparse.ArgumentTypeError(f"Couldn't find enum {values} from {self._enum}.")
		setattr(namespace, self.dest, value)

class BaseCommander(cmd2.Cmd):
	def __init__(self, pico: comm.robot.PicoBase):
		shortcuts = dict(cmd2.DEFAULT_SHORTCUTS)
		shortcuts.update({'exit': 'quit'})
		super(BaseCommander, self).__init__()
		self.pico = pico
		self.started = False

	@cmd2.with_category("General")
	def do_on(self, arg):
		"""Starts"""
		if self.started:
			self.poutput("Already on")
			return

		self.started = True
		self.pico.start()
		self.poutput("ON")

	@cmd2.with_category("General")
	def do_off(self, arg):
		"""Stops"""
		if not self.started:
			self.poutput("Already off")
			return

		self.started = False
		self.pico.stop()
		self.poutput("OFF")

	@cmd2.with_category("General")
	def do_quit(self, arg):
		"""Stops & quits"""
		self.poutput("Adios")
		self.do_off(arg)
		return True

	@cmd2.with_category("Telemetry")
	def do_telems(self, arg):
		"""list all telemetry"""
		for telem in self.pico.telems.values():
			self.poutput(telem)

	def telem_choices(self):
		return list(map(lambda x: x.name,self.pico.telems.values()))+["all"]

	stelem_parser = cmd2.Cmd2ArgumentParser()
	stelem_parser.add_argument('telem', type=str, choices_provider=telem_choices, help="Index/name of telemetry or 'all'")
	stelem_parser.add_argument('enabled', type=str2bool)

	@cmd2.with_argparser(stelem_parser)
	@cmd2.with_category("Telemetry")
	def do_stelem(self, arg):
		"""Turns on or off selected telemetry"""
		if arg.telem == "all":
			for telem in self.pico.telems.values():
				self.pico.set_telem(telem, arg.enabled)
			return

		try:
			idx = int(arg.telem)
			telem = self.pico.telem_from_idx(idx)
		except Exception:
			telem = self.pico.telem_from_name(arg.telem)

		if not telem:
			self.poutput("Couldn't find the telemetry")
			return

		self.pico.set_telem(telem, arg.enabled)

	stelemd_parser = cmd2.Cmd2ArgumentParser()
	stelemd_parser.add_argument('telem', type=str, choices_provider=telem_choices, help="Index/name of telemetry or 'all'")
	stelemd_parser.add_argument('downsample', type=int)

	@cmd2.with_argparser(stelemd_parser)
	@cmd2.with_category("Telemetry")
	def do_stelemd(self, arg):
		"""Changes the downsampling of the selected telemetry"""
		if arg.telem == "all":
			for telem in self.pico.telems.values():
				self.pico.set_telem_downsample(telem, arg.downsample)
			return

		try:
			idx = int(arg.telem)
			telem = self.pico.telem_from_idx(idx)
		except Exception:
			telem = self.pico.telem_from_name(arg.telem)

		if not telem:
			self.poutput("Couldn't find the telemetry")
			return

		self.pico.set_telem_downsample(telem, arg.downsample)

	@cmd2.with_category("Debug")
	def do_ready(self, arg):
		"""ready: checks if the robot is ready to receive a new order"""
		val = self.pico.ready_for_order()
		if val:
			self.poutput("Ready")
		else:
			self.poutput("Not Ready")

	sb_parser = cmd2.Cmd2ArgumentParser()
	sb_parser.add_argument('blocking', type=str2bool)

	@cmd2.with_argparser(sb_parser)
	@cmd2.with_category("Debug")
	def do_sb(self, arg):
		"""enables/disables blocking on commands"""
		self.pico.set_blocking(arg.blocking)


class AsservCommander(BaseCommander):
	pico: comm.robot.Asserv

	def __init__(self, asserv: comm.robot.Asserv):
		super(AsservCommander, self).__init__(asserv)

	@cmd2.with_category("Asserv")
	def do_pos(self, arg):
		"""Returns the position of the Asserv Pico"""
		dst,theta = self.pico.get_pos()
		self.poutput(f"theta: {math.degrees(theta):.2f}° dst: {dst:.2f}mm")

	@cmd2.with_category("Asserv")
	def do_posx(self, arg):
		"""Returns the position of the Asserv Pico in X,Y"""
		x,y = self.pico.get_pos_xy()
		self.poutput(f"x,y: {x:.2f}, {y:.2f}mm")

	move_parser = cmd2.Cmd2ArgumentParser()
	move_parser.add_argument('theta', type=float, help="Angle in degrees")
	move_parser.add_argument('distance', type=float, help="Distance in mm")

	@cmd2.with_argparser(move_parser)
	@cmd2.with_category("Asserv")
	def do_move(self, arg):
		"""Move the robot with polar coords"""
		if not self.started:
			self.poutput("Asserv not started")
			return

		theta, dst = arg.theta, arg.distance
		theta = math.radians(theta)

		self.poutput(f"Moving theta:{theta}rad and rho:{dst}mm")
		self.pico.move(dst, theta)

	@cmd2.with_category("Asserv Tuning")
	def do_pids(self, arg):
		"""list all pids"""
		for pid in self.pico.pids.values():
			self.poutput(pid)

	def pid_choices(self):
		return list(map(lambda x: x.name,self.pico.pids.values()))

	gpid_parser = cmd2.Cmd2ArgumentParser()
	gpid_parser.add_argument('pid', type=str, choices_provider=pid_choices, help="PID name/idx")

	@cmd2.with_argparser(gpid_parser)
	@cmd2.with_category("Asserv Tuning")
	def do_gpid(self, arg):
		"""Get PID data"""
		try:
			idx = int(arg.pid)
			pid = self.pico.pid_from_idx(idx)
		except Exception:
			pid = self.pico.pid_from_name(arg.pid)

		if not pid:
			self.poutput("Couldn't find PID")
			return

		self.pico.get_pid(pid)
		self.poutput(pid)

	spid_parser = cmd2.Cmd2ArgumentParser()
	spid_parser.add_argument('pid', type=str, choices_provider=pid_choices, help="PID name/idx")
	spid_parser.add_argument('kp', type=float, help="Kp coefficient")
	spid_parser.add_argument('ki', type=float, help="Ki coefficient")
	spid_parser.add_argument('kd', type=float, help="Kd coefficient")

	@cmd2.with_argparser(spid_parser)
	@cmd2.with_category("Asserv Tuning")
	def do_spid(self, arg):
		"""Set PID values"""
		try:
			idx = int(arg.pid)
			pid = self.pico.pid_from_idx(idx)
		except Exception:
			pid = self.pico.pid_from_name(arg.pid)

		if not pid:
			self.poutput("Wrong PID")
			return

		pid.set(arg.kp, arg.ki, arg.kd)
		self.poutput(pid)
		self.pico.set_pid(pid)

	@cmd2.with_category("Asserv Tuning")
	def do_gdsp(self, arg):
		"""Gets dst speed profile vmax and amax"""
		vmax, amax = self.pico.get_dst_speedprofile()

		self.poutput(f"vmax:{vmax}mm/s amax:{amax}mm/s²")

	@cmd2.with_category("Asserv Tuning")
	def do_gasp(self, arg):
		"""Gets angle speed profile vmax and amax"""
		vmax, amax = self.pico.get_angle_speedprofile()

		self.poutput(f"vmax:{vmax}rad/s amax:{amax}rad/s²")

	sdsp_parser = cmd2.Cmd2ArgumentParser()
	sdsp_parser.add_argument('vmax', type=float, help="Max velocity in mm/s")
	sdsp_parser.add_argument('amax', type=float, help="Max acceleration in mm/s²")

	@cmd2.with_argparser(sdsp_parser)
	@cmd2.with_category("Asserv Tuning")
	def do_sdsp(self, arg):
		"""Sets dst speed profile"""
		self.pico.set_dst_speedprofile(arg.vmax, arg.amax)

	sasp_parser = cmd2.Cmd2ArgumentParser()
	sasp_parser.add_argument('vmax', type=float, help="Max angular velocity in rad/s")
	sasp_parser.add_argument('amax', type=float, help="Max angular acceleration in rad/s²")

	@cmd2.with_argparser(sasp_parser)
	@cmd2.with_category("Asserv Tuning")
	def do_sasp(self, arg):
		"""Sets angle speed profile"""
		self.pico.set_angle_speedprofile(arg.vmax, arg.amax)

	@cmd2.with_category("Debug")
	def do_denc(self, arg):
		"""Gets encoder ticks"""
		left, right = self.pico.debug_get_encoders()

		self.poutput(f"Left: {left}, Right: {right}")

	dmot_parser = cmd2.Cmd2ArgumentParser()
	dmot_parser.add_argument('left', type=float, help="Left motor value -1.0 - 1.0")
	dmot_parser.add_argument('right', type=float, help="Right motor value -1.0 - 1.0")

	@cmd2.with_argparser(dmot_parser)
	@cmd2.with_category("Debug")
	def do_dmot(self, arg):
		"""Set motor values"""
		self.pico.debug_set_motors(arg.left, arg.right)

	dmote_parser = cmd2.Cmd2ArgumentParser()
	dmote_parser.add_argument('enabled', type=str2bool)

	@cmd2.with_argparser(dmote_parser)
	@cmd2.with_category("Debug")
	def do_dmote(self, arg):
		"""Enables or disables the motor drivers"""
		self.pico.debug_set_motors_enable(arg.enabled)

	@cmd2.with_category("Debug")
	def do_dstate(self, arg):
		"""Returns the state of the controller"""
		state = self.pico.debug_get_controller_state()
		state = ["Reaching Theta", "Reaching Dst", "Reached target"][state]
		self.poutput(f"State: {state}")

	@cmd2.with_category("Debug")
	def do_dbg(self, arg):
		"""Prints the debug info for each BG Driver"""
		vel, curr, temp, vbus = self.pico.debug_get_left_bg_stats()
		self.poutput(f"Left  BG: {vel:.2f}rad/s, {curr:.2f}A, {vbus:.2f}V, {temp:.2f}°C")
		vel, curr, temp, vbus = self.pico.debug_get_right_bg_stats()
		self.poutput(f"Right BG: {vel:.2f}rad/s, {curr:.2f}A, {vbus:.2f}V, {temp:.2f}°C")

	@cmd2.with_category("Asserv")
	def do_estop(self, arg):
		"""Sends an emergency stop"""
		self.pico.emergency_stop()

	movea_parser = cmd2.Cmd2ArgumentParser()
	movea_parser.add_argument('x', type=float, help="X Coord of point to move to")
	movea_parser.add_argument('y', type=float, help="Y Coord of point to move to")

	@cmd2.with_argparser(movea_parser)
	@cmd2.with_category("Asserv")
	def do_movea(self, arg):
		"""Move to the absolute coords in a straight line"""
		if not self.started:
			self.poutput("Asserv not started")
			return

		self.pico.move_abs(arg.x, arg.y)

	sq_parser = cmd2.Cmd2ArgumentParser()
	sq_parser.add_argument('length', type=float, help="Side length of the square in mm")

	@cmd2.with_argparser(sq_parser)
	@cmd2.with_category("Asserv")
	def do_sq(self, arg):
		"""Make a square"""
		for i in range(4):
			self.poutput(i)
			self.pico.move(arg.length, 0)
			#time.sleep(2)
			self.pico.move(0, math.radians(90))
			#time.sleep(2)

	deff_parser = cmd2.Cmd2ArgumentParser()
	deff_parser.add_argument('controlState', type=comm.robot.ControlState, default=comm.robot.ControlState.MANUAL, action=EnumAction, help="Control state of the effects")
	deff_parser.add_argument('blinker', type=comm.robot.BlinkerState, default=comm.robot.BlinkerState.OFF, action=EnumAction, help="Blinker state")
	deff_parser.add_argument('stop', type=str2bool, default=False, help="Stop light state")
	deff_parser.add_argument('centerStop', type=str2bool, default=False, help="Center stop light on/off")
	deff_parser.add_argument('headlight', type=comm.robot.HeadlightState, default=comm.robot.HeadlightState.OFF, action=EnumAction, help="Headlight state")
	deff_parser.add_argument('ring', type=comm.robot.RingState, default=comm.robot.RingState.OFF, action=EnumAction, help="Ring light state")
	deff_parser.add_argument('disco', type=str2bool, default=False, help="Disco mode toggle")
	deff_parser.add_argument('reversing', type=str2bool, default=False, help="Reversing on/off")
	deff_parser.add_argument('smoke', type=str2bool, default=False, help="Smoke on/off")

	@cmd2.with_argparser(deff_parser)
	@cmd2.with_category("Effects")
	def do_deff(self, arg):
		"""Control effects states	"""
		self.pico.debug_set_effects(arg.controlState, arg.blinker, arg.stop, arg.centerStop, arg.headlight, arg.ring, arg.disco, arg.reversing, arg.smoke)

	drgb_parser = cmd2.Cmd2ArgumentParser()
	drgb_parser.add_argument('rgb', type=hex2int, help="RGB hex value")
	drgb_parser.add_argument('brightness', type=int, default=255, help="Brightness value 0-255")

	@cmd2.with_argparser(drgb_parser)
	@cmd2.with_category("Effects")
	def do_drgb(self, arg):
		"""Sets all the LEDs to a single RGB value to debug"""
		self.pico.debug_set_rgb(arg.rgb, arg.brightness)

	@cmd2.with_category("Effects")
	def do_dea(self, arg):
		"""Go to effect auto"""
		self.pico.debug_set_effects(comm.robot.ControlState.AUTOMATIC)

	@cmd2.with_category("Effects")
	def do_dem(self, arg):
		"""Go to effect manual"""
		self.pico.debug_set_effects(comm.robot.ControlState.MANUAL)

	@cmd2.with_category("Effects")
	def do_gay(self, arg):
		"""Gay mode"""
		self.pico.debug_set_effects(comm.robot.ControlState.GAY)

	@cmd2.with_category("Effects")
	def do_straight(self, arg):
		"""Go back to normal auto mode"""
		self.do_dea(arg)

	dpu_parser = cmd2.Cmd2ArgumentParser()
	dpu_parser.add_argument('left', type=float, help="Left servo value -1 to 1")
	dpu_parser.add_argument('right', type=float, help="Right servo value -1 to 1")

	@cmd2.with_argparser(dpu_parser)
	@cmd2.with_category("Effects")
	def do_dpu(self, arg):
		"""Set raw values of servos for the pop up headlights"""
		self.pico.debug_set_popup(arg.left, arg.right)


class ActionCommander(BaseCommander):
	pico: comm.robot.Action

	def __init__(self, action: comm.robot.Action):
		super(ActionCommander, self).__init__(action)

	@cmd2.with_category("Actuators")
	def do_demo(self, arg):
		"""Random demo time"""
		self.pico.start()

		self.pico.pump_enable(0, True)
		self.poutput("pe")
		time.sleep(1)
		self.pico.pump_enable(0, False)
		self.poutput("pd")

		time.sleep(1)

		self.pico.elev_home()
		self.poutput("eh")
		time.sleep(0.5)

		self.pico.elev_move_abs(125)
		self.poutput("emove")
		time.sleep(0.5)

		self.pico.elev_move_abs(65)
		self.poutput("emove")
		time.sleep(0.5)

		self.pico.elev_move_abs(0)
		self.poutput("emove")
		time.sleep(0.5)

		self.pico.elev_home()
		self.poutput("eh")

		time.sleep(1)

		self.pico.right_arm_fold()
		self.poutput("af")
		time.sleep(1)

		self.pico.right_arm_deploy()
		self.poutput("ad")
		time.sleep(1)

		self.pico.right_arm_turn(360)
		self.poutput("at")
		time.sleep(0.5)
		self.pico.right_arm_turn(-180)
		self.poutput("at")
		time.sleep(0.5)

		self.pico.right_arm_fold()
		self.poutput("af")

		self.pico.stop()

	@cmd2.with_category("Actuators: Elevator")
	def do_ehomed(self, arg):
		"""Is elevator homed ?"""
		homed = self.pico.elev_homed()
		self.poutput("Homed" if homed else "Not Homed")

	@cmd2.with_category("Actuators: Elevator")
	def do_epos(self, arg):
		"""Position of elevator (in mm)"""
		pos = self.pico.elev_pos()
		self.poutput(f"pos:{pos}mm")

	@cmd2.with_category("Actuators: Elevator")
	def do_ehome(self, arg):
		"""Homes the elevator, needed before moving"""
		self.pico.elev_home()

	emove_parser = cmd2.Cmd2ArgumentParser()
	emove_parser.add_argument('pos', type=float, help="Elevator pos in mm")

	@cmd2.with_argparser(emove_parser)
	@cmd2.with_category("Actuators: Elevator")
	def do_emove(self, arg):
		"""Absolute position elevator move"""
		self.pico.elev_move_abs(arg.pos)

	emover_parser = cmd2.Cmd2ArgumentParser()
	emover_parser.add_argument('dst', type=float, help="Relative move in mm")

	@cmd2.with_argparser(emover_parser)
	@cmd2.with_category("Actuators: Elevator")
	def do_emover(self, arg):
		"""Relative position elevator move"""
		self.pico.elev_move_rel(arg.dst)

	@cmd2.with_category("Actuators: Arms")
	def do_ardeployed(self, arg):
		"""Is right arm deployed ?"""
		deployed = self.pico.right_arm_deployed()
		self.poutput("Arm deployed" if deployed else "Arm not deployed (not necessarly folded)")

	@cmd2.with_category("Actuators: Arms")
	def do_arangles(self, arg):
		"""Get right arm angles, deployed and turn in degrees"""
		dep, turn = self.pico.right_arm_angles()
		self.poutput(f"deploy:{dep}deg, turn:{turn}deg")

	@cmd2.with_category("Actuators: Arms")
	def do_ardeploy(self, arg):
		"""Deploys the right arm"""
		self.pico.right_arm_deploy()

	@cmd2.with_category("Actuators: Arms")
	def do_arhdeploy(self, arg):
		"""Half deploys the right arm"""
		self.pico.right_arm_half_deploy()

	@cmd2.with_category("Actuators: Arms")
	def do_arfold(self, arg):
		"""Folds the right arm in compact position"""
		self.pico.right_arm_fold()

	arturn_parser = cmd2.Cmd2ArgumentParser()
	arturn_parser.add_argument('angle', type=float, help="Turn angle in deg")

	@cmd2.with_argparser(arturn_parser)
	@cmd2.with_category("Actuators: Arms")
	def do_arturn(self, arg):
		"""Turn right arm head by angle"""
		self.pico.right_arm_turn(arg.angle)

	@cmd2.with_category("Actuators: Arms")
	def do_aldeployed(self, arg):
		"""Is left arm deployed ?"""
		deployed = self.pico.left_arm_deployed()
		self.poutput("Arm deployed" if deployed else "Arm not deployed (not necessarly folded)")

	@cmd2.with_category("Actuators: Arms")
	def do_alangles(self, arg):
		"""Get left arm angles, deployed and turn in degrees"""
		dep, turn = self.pico.left_arm_angles()
		self.poutput(f"deploy:{dep}deg, turn:{turn}deg")

	@cmd2.with_category("Actuators: Arms")
	def do_aldeploy(self, arg):
		"""Deploys the left arm"""
		self.pico.left_arm_deploy()

	@cmd2.with_category("Actuators: Arms")
	def do_alhdeploy(self, arg):
		"""Half deploys the left arm"""
		self.pico.left_arm_half_deploy()

	@cmd2.with_category("Actuators: Arms")
	def do_alfold(self, arg):
		"""Folds the left arm in compact position"""
		self.pico.left_arm_fold()

	alturn_parser = cmd2.Cmd2ArgumentParser()
	alturn_parser.add_argument('angle', type=float, help="Turn angle in deg")

	@cmd2.with_argparser(alturn_parser)
	@cmd2.with_category("Actuators: Arms")
	def do_alturn(self, arg):
		"""Turn left arm head by angle"""
		self.pico.left_arm_turn(arg.angle)

	pump_parser = cmd2.Cmd2ArgumentParser()
	pump_parser.add_argument('idx', type=int, help="Pump index")
	pump_parser.add_argument('state', type=str2bool, help="Pump state")

	@cmd2.with_argparser(pump_parser)
	@cmd2.with_category("Actuators: Succ")
	def do_pump(self, arg):
		"""Sets the pump state"""
		self.pico.pump_enable(arg.idx, arg.state)


if __name__ == "__main__":
	# Build the right commander
	parser = argparse.ArgumentParser(prog='Commander',
			description='Debug tool to talk to the picos')

	parser.add_argument('-a', '--action', action='store_true', help='Run the action pico commander')
	parser.add_argument('-d', '--debug', action='store_true', help='Enables the screen debug')

	args = parser.parse_args()

	action = None
	asserv = None

	print("Connecting to Pico...")
	if args.action:
		action = comm.make_action()
		commander = ActionCommander(action)
	else:
		asserv = comm.make_asserv()
		commander = AsservCommander(asserv)
	print("Connected")

	if args.debug:
		scr_handler = handlers.DisplayHandler(action=action, asserv=asserv, debug=True, thread=True)
		scr_handler.start()

	# Run the cmd loop
	try:
		commander.cmdloop()
	except KeyboardInterrupt:
		print("CTRL-C, shutting down")
		commander.do_off(None)
	finally:
		# When we finish, even if we crash, stop the pico
		commander.pico.stop()