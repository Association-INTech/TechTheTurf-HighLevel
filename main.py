import time, math
import RPi.GPIO as GPIO
import hokuyolx, threading
import numpy as np

import comm

# ======== Settings ========

# :)
LIDAR_ENABLE = False
# Side
BLUE_SIDE = False
# Only run on negative edge of jumper switch
JUMPER_SAFE = False
# Continues after the obstacle is no more
RESTART_AFTER_OBS_CLEAR = False
# Pretty self explanatory
LIDAR_DETECT_RADIUS = 200
# in s, the time the big robot can move
MATCH_PLAY_TIME = 90
# Wait time between every instruction, in s
INST_WAIT = 1
# Offset to the border of the table
BORDER_SETUP_OFFSET = 30

# ===========================
# Physical constants
TABLE_WIDTH = 1000
TABLE_LENGTH = 3000

ROBOT_WIDTH = 200
ROBOT_LENGTH = 350
ENCODER_OFFSET_TO_FRONT = 145
LIDAR_OFFSET_TO_FRONT = 125
ARM_OFFSET_TO_FRONT = 135.5


# Electrical constants
JUMPER_PIN = 22

# Global variable that tells the state
SCENARIO_STARTED = False

# We start off at the bottom left or right corner of the table facing forwards
# So the X is unchanged but Y is flipped when we are on the bottom right, so Yellow team
Y_DIR = 1 if BLUE_SIDE else -1

LIDAR_DETECT_RADIUS_SQ = LIDAR_DETECT_RADIUS*LIDAR_DETECT_RADIUS

GPIO.setmode(GPIO.BCM)
# Jumper in input Pull-Up
GPIO.setup(JUMPER_PIN, GPIO.IN, GPIO.PUD_UP)

def wait_for_jumper():
	global SCENARIO_STARTED
	if JUMPER_SAFE and GPIO.input(JUMPER_PIN):
		print("Waiting for jumper to be inserted...")

		while GPIO.input(JUMPER_PIN):
			time.sleep(0.01)

		time.sleep(1)

	print("Waiting for start...")

	while not GPIO.input(JUMPER_PIN):
		time.sleep(0.01)

	print("Starting")

	SCENARIO_STARTED = True

def get_pos_xy_table(pico, extra_xoff=0, extra_yoff=0):
	dst, theta = pico.get_pos()
	x,y = pico.get_pos_xy()
	x_off = ROBOT_LENGTH - ENCODER_OFFSET_TO_FRONT + extra_xoff
	y_off = Y_DIR*(ROBOT_WIDTH/2.0 + extra_yoff)
	cos_tht = math.cos(theta)
	sin_tht = math.sin(theta)
	x += cos_tht*x_off - sin_tht*y_off
	y += sin_tht*x_off + cos_tht*y_off + Y_DIR*BORDER_SETUP_OFFSET
	return x,y,theta

def lidar_thread(pico, lidar_ready):
	lidar = hokuyolx.HokuyoLX()
	while True:
		try:
			ts, dsts = lidar.get_filtered_dist(dmax=3000)
			x,y,theta = get_pos_xy_table(pico, ENCODER_OFFSET_TO_FRONT-LIDAR_OFFSET_TO_FRONT)
			y *= Y_DIR

			# We successfully check once, we are ready
			if not lidar_ready.is_set():
				lidar_ready.set()

			detected = None
			for ang, dst in dsts[50:-50]:
				px = x + dst*math.cos(theta+ang)
				py = y + Y_DIR*dst*math.sin(theta+ang)

				if px < 0 or px > TABLE_LENGTH or py < 0 or py > TABLE_WIDTH:
					continue

				if dst > LIDAR_DETECT_RADIUS:
					continue

				detected = dst,px,py
				break

			print(x,y,theta)
			if detected is not None:
				print(f"Obs {detected}")
				if SCENARIO_STARTED:
					pico.notify_stop()
			elif SCENARIO_STARTED and RESTART_AFTER_OBS_CLEAR:
				pico.notify_stop_clear()
		except Exception as e:
			print(f"Lidar thread Exception: {e}")

def move_abs(pico, tx, ty):
	dst, theta = pico.get_pos()
	cx, cy = pico.get_pos_xy()
	dx = tx - cx
	dy = ty - cy

	theta %= 2*math.pi

	deltaTheta = (math.atan2(dy, dx)-theta)%(2*math.pi)
	deltaDst = math.sqrt(dx * dx + dy * dy)

	if deltaTheta > math.pi:
		deltaTheta = 2*math.pi - deltaTheta
	elif deltaTheta < -math.pi:
		deltaTheta = 2*math.pi + deltaTheta

	print(f"Moving {deltaTheta}rads, {deltaDst}mm")
	pico.move(deltaDst, deltaTheta)

# Example scenario

print(f"Running {'Blue' if BLUE_SIDE else 'Yellow'} side scenario.")

asserv = comm.make_asserv()
action = comm.make_action()

if LIDAR_ENABLE:
	lidar_ready = threading.Event()
	lidar_thread = threading.Thread(target=lidar_thread, args=(asserv,lidar_ready), daemon=True)
	lidar_thread.start()

	print("Waiting for LIDAR...")
	lidar_ready.wait()
	print("LIDAR ready.")

asserv.start()
action.start()

action.arm_fold()

try:
	wait_for_jumper()
	start_time = time.time()

	#asserv.move(275-(ROBOT_LENGTH-ARM_OFFSET_TO_FRONT), 0)
	asserv.move(215, 0)
	time.sleep(INST_WAIT)
	for i in range(3):
		action.arm_deploy()
		time.sleep(INST_WAIT)
		action.arm_turn(Y_DIR*90)
		time.sleep(INST_WAIT)
		action.arm_fold()
		time.sleep(INST_WAIT)

		if i != 2:
			asserv.move(220, 0)
			time.sleep(INST_WAIT)

	asserv.move(0, math.radians(Y_DIR*90))
	time.sleep(INST_WAIT)
	asserv.move(400-BORDER_SETUP_OFFSET, 0)
	time.sleep(INST_WAIT)
	asserv.move(550, math.radians(-Y_DIR*90))
	time.sleep(INST_WAIT)
	asserv.move(600, math.radians(Y_DIR*90))
	time.sleep(INST_WAIT)
	move_abs(asserv, 10, 0)
	time.sleep(INST_WAIT)

	left = MATCH_PLAY_TIME - (time.time()-start_time)
	print(f"Finished, let's chill until the end, {left:.2f}s left")
	time.sleep(left)

finally:
	print("Stopping everything")
	asserv.stop()
	action.stop()