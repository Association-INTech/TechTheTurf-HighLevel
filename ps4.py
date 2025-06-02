import time
import sys
import math

import comm
from comm.robot import RingState
import utils.gamepad as pad

UPDATE_FREQ = 100.0
DEADZONE = 0.1
PAMI = False
ACTION_ENABLED = True
ARM_HALF = False

if len(sys.argv) > 1:
	if sys.argv[1] == "p":
		PAMI = True
	elif sys.argv[1] == "na":
		ACTION_ENABLED = False

if PAMI:
	ACTION_ENABLED = False

asserv = comm.make_asserv()
asserv.set_blocking(False)
if ACTION_ENABLED:
	action = comm.make_action()
	action.set_blocking(False)

class LimitedValue:
	def __init__(self, max_deriv, max_deriv_minus=None):
		self.max_deriv = max_deriv
		if max_deriv_minus is None:
			self.max_deriv_minus = max_deriv
		else:
			self.max_deriv_minus = max_deriv_minus
		self.reset()

	def apply(self, val, dt):
		cderiv = (val-self.prev)/dt
		if cderiv > self.max_deriv or cderiv < -self.max_deriv_minus:
			cderiv = -self.max_deriv_minus if cderiv < 0 else self.max_deriv
			val = self.prev+cderiv*dt
		self.prev = val
		return val

	def add(self, val, dt):
		return self.apply(self.prev+val, dt)

	def val(self):
		return self.prev

	def reset(self):
		self.prev = 0

# Speed setup
if PAMI:
	prec_speed_remove = 400 # mm/s
	prec_turn_remove = 1.5 # rad/s
	turbo_speed_add = 400 # mm/s
	move_speed = 500 # mm/s
	turn_speed = 2 # rad/s
	speed_accel_lim = 2000 # mm^2/s
else:
	prec_speed_remove = 300 # mm/s
	prec_turn_remove = 1.5 # rad/s
	turbo_speed_add = 300 # mm/s
	move_speed = 400 # mm/s
	turn_speed = 2 # rad/s
	arm_turn_speed = 600 # deg/s
	speed_accel_lim = 1000 # mm^2/s

# Gamepad setup
gamepadType = pad.PS4
#gamepadType = pad.VaderXinput
btnDeploy = "CROSS"
btnLeftArm = "L1"
btnRightArm = "R1"
btnExit = "OPTIONS"
joySpeed = "LEFT-Y"
joyTurn = "RIGHT-X"
joyTurbo = "R2"
joySlow = "L2"
joyArmLeftTurn = "DPAD-Y"
joyArmRightTurn = "DPAD-X"
btnWarning = "TRIANGLE"
btnHeadlights = "SQUARE"
btnPro = "CIRCLE"
btnSmoke = "R3"
btnPopUp = "L3"

# State variables
dstVel = LimitedValue(speed_accel_lim)
dst = 0
theta = 0
leftArmState = False
rightArmState = False

# Dt variables
st = -1/UPDATE_FREQ
end = 0

# Wait for a connection
if not pad.available():
	print('Please connect your gamepad...')
	while not pad.available():
		time.sleep(1.0)
gamepad = gamepadType()
print("Gamepad connected")

#asserv.start()
#asserv.wait_completed()

#time.sleep(1)

#print("Asserv started")

if ACTION_ENABLED:
	action.start()
	action.wait_completed()
	
	print("Action started")

	if ARM_HALF:
		action.left_arm_half_deploy()
		action.wait_completed()
		action.right_arm_half_deploy()
		action.wait_completed()
	else:
		action.left_arm_fold()
		action.wait_completed()
		action.right_arm_fold()
		action.wait_completed()

	print("Arm folded")


gamepad.startBackgroundUpdates()

def deadzone(val):
	if abs(val) < DEADZONE:
		return 0
	return val

def trigger(val):
	return (val+1.0)/2.0

state = True
proMode = True

asserv.debug_set_motors_enable(True)

try:
	controlState = comm.robot.ControlState.MANUAL
	blinkState = comm.robot.BlinkerState.OFF
	lastArmRightTurn = 0
	lastArmLeftTurn = 0
	headlightState = comm.robot.HeadlightState.OFF
	ringState = comm.robot.RingState.OFF
	smoking = False
	popAdjust = False
	while gamepad.isConnected():
		dt = end-st
		st = time.time()

		if gamepad.beenPressed(btnExit):
			state = not state
			if proMode:
				for i in range(50):
					asserv.debug_set_motors_enable(state)
			else:
				asserv.set_running(state)
			dst = 0
			theta = 0
			dstVel.reset()
			print(f"State is {state}")

		if gamepad.beenPressed(btnPro) and state:
			if proMode:
				for i in range(50):
					asserv.debug_set_motors_enable(False)
				asserv.set_running(True)
				asserv.wait_completed()
				dst = 0
				theta = 0
				dstVel.reset()
				proMode = False
				print("ProMode off")
			else:
				asserv.set_running(False)
				asserv.wait_completed()
				for i in range(50):
					asserv.debug_set_motors_enable(True)
				proMode = True
				print("ProMode on")

		if ACTION_ENABLED:
			if gamepad.beenPressed(btnLeftArm):
				if not leftArmState:
					action.left_arm_deploy()
					leftArmState = True
				else:
					if ARM_HALF:
						action.left_arm_half_deploy()
					else:
						action.left_arm_fold()
					leftArmState = False

			if gamepad.beenPressed(btnRightArm):
				if not rightArmState:
					action.right_arm_deploy()
					rightArmState = True
				else:
					if ARM_HALF:
						action.right_arm_half_deploy()
					else:
						action.right_arm_fold()
					rightArmState = False

		if gamepad.beenPressed(btnPopUp):
			popAdjust = not popAdjust
			print(f"PopAdj: {popAdjust}")

		speed = -deadzone(gamepad.axis(joySpeed))
		turn = -deadzone(gamepad.axis(joyTurn))
		turbo = trigger(gamepad.axis(joyTurbo))
		slow = trigger(gamepad.axis(joySlow))
		armLeftTurn = deadzone(gamepad.axis(joyArmLeftTurn))
		armRightTurn = deadzone(gamepad.axis(joyArmRightTurn))

		move_spd_adj = move_speed
		turn_spd_adj = turn_speed
		if not popAdjust:
			move_spd_adj += turbo_speed_add*turbo - prec_speed_remove*slow
			turn_spd_adj -= prec_turn_remove*slow

		dstVelVal = dstVel.apply(move_spd_adj*speed,dt)
		stopping = abs(dstVelVal) > 0 and speed == 0
		reversing = abs(dstVelVal) > 0 and speed < 0
		dst += dstVelVal*dt
		theta += turn_spd_adj*turn*dt

		#print(dst, theta)

		if ACTION_ENABLED:
			if armLeftTurn != 0:
				action.left_arm_turn(arm_turn_speed*armLeftTurn*dt)
			if armRightTurn != 0:
				action.right_arm_turn(arm_turn_speed*armRightTurn*dt)

		if proMode:
			scaling = 1.0 if PAMI else 20.0+120.0*turbo-5.0*slow
			asserv.debug_set_motors(scaling * (speed * math.cos(math.pi/4) - turn * math.sin(math.pi/4)), scaling * (speed * math.sin(math.pi/4) + turn * math.cos(math.pi/4)))
		else:
			asserv.debug_set_target(dst, theta)

		if PAMI:
			if gamepad.beenPressed(btnWarning):
				if blinkState == comm.robot.BlinkerState.WARNING:
					blinkState = comm.robot.BlinkerState.OFF
				else:
					blinkState = comm.robot.BlinkerState.WARNING
			elif armRightTurn < 0 and lastArmRightTurn >= 0:
				if blinkState == comm.robot.BlinkerState.LEFT:
					blinkState = comm.robot.BlinkerState.OFF
				else:
					blinkState = comm.robot.BlinkerState.LEFT
			elif armRightTurn > 0 and lastArmRightTurn <= 0:
				if blinkState == comm.robot.BlinkerState.RIGHT:
					blinkState = comm.robot.BlinkerState.OFF
				else:
					blinkState = comm.robot.BlinkerState.RIGHT

			if gamepad.beenPressed(btnHeadlights):
				if headlightState == comm.robot.HeadlightState.OFF:
					headlightState = comm.robot.HeadlightState.DIM
				elif headlightState == comm.robot.HeadlightState.DIM:
					headlightState = comm.robot.HeadlightState.FULL
				elif headlightState == comm.robot.HeadlightState.FULL:
					headlightState = comm.robot.HeadlightState.OFF

			if gamepad.beenPressed(btnDeploy):
				if controlState == comm.robot.ControlState.MANUAL:
					controlState = comm.robot.ControlState.GAY
				else:
					controlState = comm.robot.ControlState.MANUAL

			if armLeftTurn < 0 and lastArmLeftTurn >= 0:
				try:
					ringState = comm.robot.RingState(ringState.value+1)
				except Exception:
					ringState = comm.robot.RingState.OFF

			if gamepad.beenPressed(btnSmoke):
				smoking = not smoking

			leftPop = 1 if headlightState != comm.robot.HeadlightState.OFF else 0
			rightPop = 1 if headlightState != comm.robot.HeadlightState.OFF else 0

			if popAdjust:
				fact = 1 if headlightState == comm.robot.HeadlightState.OFF else -1
				leftPop += slow*fact
				rightPop += turbo*fact

			lastArmRightTurn = armRightTurn
			lastArmLeftTurn = armLeftTurn

			asserv.debug_set_effects(controlState, blinkState, stopping, True, headlightState, ringState, False, reversing, smoking, leftPop, rightPop)
		time.sleep(1.0/UPDATE_FREQ)
		end = time.time()

except Exception as e:
	print(f"Exception: {e}")
finally:
	print("Closing")
	gamepad.disconnect()

	asserv.debug_set_motors_enable(False)
	asserv.debug_set_effects(comm.robot.ControlState.AUTOMATIC, comm.robot.BlinkerState.OFF, False, True, comm.robot.HeadlightState.OFF, comm.robot.RingState.OFF)
	asserv.stop()
	asserv.wait_completed()

	if ACTION_ENABLED:
		action.stop()
		action.wait_completed()