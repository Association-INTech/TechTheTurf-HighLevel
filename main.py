import time, math
import RPi.GPIO as GPIO

import comm

JUMPER_PIN = 22
SAFE = True

GPIO.setmode(GPIO.BCM)
# Jumper in input Pull-Up
GPIO.setup(JUMPER_PIN, GPIO.IN, GPIO.PUD_UP)

def wait_for_jumper():
	if SAFE and GPIO.input(JUMPER_PIN):
		print("Waiting for jumper to be inserted...")

		while GPIO.input(JUMPER_PIN):
			time.sleep(0.01)

		time.sleep(1)

	print("Waiting for start...")

	while not GPIO.input(JUMPER_PIN):
		time.sleep(0.01)

	print("Starting")

# Example scenario

asserv = comm.make_asserv()

asserv.start()

wait_for_jumper()

side_len = 500 # mm

for i in range(4):
	print(i)
	asserv.move(side_len, 0)
	time.sleep(2)
	asserv.move(0, math.radians(90))
	time.sleep(2)

asserv.stop()