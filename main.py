import time, math
import RPi.GPIO as GPIO
import hokuyolx, threading
import numpy as np

import comm

JUMPER_PIN = 22
JUMPER_SAFE = True

GPIO.setmode(GPIO.BCM)
# Jumper in input Pull-Up
GPIO.setup(JUMPER_PIN, GPIO.IN, GPIO.PUD_UP)

def wait_for_jumper():
	if JUMPER_SAFE and GPIO.input(JUMPER_PIN):
		print("Waiting for jumper to be inserted...")

		while GPIO.input(JUMPER_PIN):
			time.sleep(0.01)

		time.sleep(1)

	print("Waiting for start...")

	while not GPIO.input(JUMPER_PIN):
		time.sleep(0.01)

	print("Starting")

def lidar_thread(pico):
	lidar = hokuyolx.HokuyoLX()
	while True:
		ts, dsts = lidar.get_filtered_dist(dmax=3000)
		sm = np.min(dsts.T[1][100:-100])
		if sm < 300:
			print(f"Obs {sm}")
			pico.notify_stop()
		else:
			pico.notify_stop_clear()

# Example scenario

asserv = comm.make_asserv()

lidar_thread = threading.Thread(target=lidar_thread, args=(asserv,), daemon=True)
lidar_thread.start()

asserv.start()

try:
	wait_for_jumper()

	side_len = 400 # mm

	for i in range(4):
		print(f"Side {i}, moving distance")
		asserv.move(side_len, 0)
		time.sleep(0.5)
		print(f"Side {i}, moving angle")
		asserv.move(0, math.radians(90))
		time.sleep(0.5)

	print("Finished, waiting 15s for asserv to settle")

	time.sleep(15)
finally:
	print("Stopping asserv")
	asserv.stop()