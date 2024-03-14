import time
import sys

import comm
import utils.gamepad as pad

UPDATE_FREQ = 100.0
DEADZONE = 0.1
ELEV_MAX = 200.0
PAMI = False
ACTION_ENABLED = True

if len(sys.argv) > 1 and sys.argv[1] == "p":
	ACTION_ENABLED = False
	PAMI = True

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
	prec_speed_remove = 300 # mm/s
	prec_turn_remove = 1.5 # rad/s
	turbo_speed_add = 400 # mm/s
	move_speed = 400 # mm/s
	turn_speed = 2 # rad/s
	speed_accel_lim = 1000 # mm^2/s
else:
	prec_speed_remove = 600 # mm/s
	prec_turn_remove = 1.5 # rad/s
	turbo_speed_add = 700 # mm/s
	move_speed = 700 # mm/s
	elev_speed = 25 # mm per button press
	turn_speed = 2 # rad/s
	arm_turn_speed = 600 # deg/s
	speed_accel_lim = 1500 # mm^2/s

# Gamepad setup
gamepadType = pad.PS4
btnDeploy = "CROSS"
btnFold = "CIRCLE"
btnPump = "TRIANGLE"
btnExit = "PS"
joySpeed = "LEFT-X"
joyTurn = "RIGHT-X"
joyTurbo = "R2"
joySlow = "L2"
joyElevator = "DPAD-Y"
joyArmTurn = "DPAD-X"

# State variables
dstVel = LimitedValue(speed_accel_lim)
dst = 0
theta = 0
pumpState = False
elevPos = 0

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

asserv.start()
asserv.wait_completed()

time.sleep(1)

print("Asserv started")

if ACTION_ENABLED:
	action.start()
	action.wait_completed()
	
	print("Action started")
	
	action.elev_home()
	action.wait_completed()
	
	print("Elev home")

gamepad.startBackgroundUpdates()

def deadzone(val):
	if abs(val) < DEADZONE:
		return 0
	return val

def trigger(val):
	return (val+1.0)/2.0

try:
	while gamepad.isConnected():
		dt = end-st
		st = time.time()

		if gamepad.beenPressed(btnExit):
			print("Exit")
			break

		if ACTION_ENABLED:
			if gamepad.beenPressed(btnDeploy):
				action.arm_deploy()

			if gamepad.beenReleased(btnFold):
				action.arm_fold()

			if gamepad.beenPressed(btnPump):
				pumpState = not pumpState
				action.pump_enable(0, pumpState)
				if pumpState is False:
					action.wait_completed()
					action.pump_enable(1, True)
					action.wait_completed()
					time.sleep(0.1)
					action.pump_enable(1, False)

		elev = deadzone(gamepad.axis(joyElevator))
		speed = deadzone(gamepad.axis(joySpeed))
		turn = -deadzone(gamepad.axis(joyTurn))
		turbo = trigger(gamepad.axis(joyTurbo))
		slow = trigger(gamepad.axis(joySlow))
		armTurn = deadzone(gamepad.axis(joyArmTurn))

		move_spd_adj = move_speed + turbo_speed_add*turbo - prec_speed_remove*slow
		turn_spd_adj = turn_speed - prec_turn_remove*slow

		dst += dstVel.apply(move_spd_adj*speed,dt)*dt
		theta += turn_spd_adj*turn*dt

		#print(dst, theta)

		if ACTION_ENABLED:
			if armTurn != 0:
				action.arm_turn(arm_turn_speed*armTurn*dt)

			if elev != 0:
				elevPos = max(min(elevPos-elev*elev_speed,ELEV_MAX),0)
				action.elev_move_abs(elevPos)
				action.wait_completed()

		asserv.debug_set_target(dst, theta)
		time.sleep(1.0/UPDATE_FREQ)
		end = time.time()

except Exception as e:
	print(f"Exception: {e}")
finally:
	print("Closing")
	gamepad.disconnect()

	asserv.stop()
	asserv.wait_completed()

	if ACTION_ENABLED:
		action.stop()
		action.wait_completed()