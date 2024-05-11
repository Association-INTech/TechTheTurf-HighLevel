import RPi.GPIO as GPIO
import threading, time
import numpy as np
import os
try:
	import hokuyolx
	from RPLCD.i2c import CharLCD
except Exception:
	# Running on pami
	pass
try:
	from hcsr04sensor import sensor
except Exception:
	# Running on main
	pass

import metacom.mqtt as mqtt

# General constants
MATCH_PLAY_TIME = 99
INST_WAIT = 1

# Physical constants
TABLE_WIDTH = 2000
TABLE_LENGTH = 3000

ROBOT_WIDTH = 200
ROBOT_LENGTH = 350
ENCODER_OFFSET_TO_FRONT = 145
LIDAR_OFFSET_TO_FRONT = 145
ARM_OFFSET_TO_FRONT = 135.5

# Paminable constants
HCSR04_OFFSET_TO_ENCODER = -50
PAMINABLE_ENCODER_OFFSET_TO_FRONT = 90

# Electrical constants
JUMPER_PIN = 22
# Paminable
HCSR04_TRIG = 23
HCSR04_ECHO = 24

LCD_ADDR = 0x3f
LCD_COLS = 20
LCD_ROWS = 4

GPIO.setmode(GPIO.BCM)

class JumperStart:
	def __init__(self, pin=JUMPER_PIN, safe=False):
		self.pin = pin
		self.safe = safe

		# Jumper in input Pull-Up
		GPIO.setup(pin, GPIO.IN, GPIO.PUD_UP)

	def state(self):
		return not GPIO.input(self.pin)

	def wait(self):
		if self.safe and GPIO.input(self.pin):
			print("Waiting for jumper to be inserted...")

			while GPIO.input(self.pin):
				time.sleep(0.01)

			time.sleep(1)

		print("Waiting for start...")

		while not GPIO.input(self.pin):
			time.sleep(0.01)

		print("Starting")

class LidarHandler:
	def __init__(self, width, length, radius, margin, pos_func, detected_func, cleared_func=None):
		self.width = width
		self.length = length
		self.radius = radius
		self.margin = margin
		self.pos_func = pos_func
		self.detected_func = detected_func
		self.cleared_func = cleared_func
		self.lidar = hokuyolx.HokuyoLX()

		self.ready = threading.Event()
		self.thread = None
		self.alive = False

	def start(self, wait_start=True):
		self.ready.clear()
		self.alive = True
		self.thread = threading.Thread(target=self.thread_func, daemon=True)
		self.thread.start()
		if wait_start:
			self.ready.wait()

	def stop(self):
		self.alive = False
		self.thread.join()
		self.thread = None
		self.ready.clear()

	def thread_func(self):
		has_detected = False
		while self.alive:
			try:
				ts, dsts = self.lidar.get_filtered_dist(dmax=max(self.width, self.length))
				x,y,theta = self.pos_func()

				# We successfully check once, we are ready
				if not self.ready.is_set():
					self.ready.set()

				detected = None
				for ang, dst in dsts:
					if abs(ang) > np.radians(60):
						continue
					px = x + dst*np.cos(theta+ang)
					py = y + dst*np.sin(theta+ang)

					if px < self.margin or px > self.length-self.margin or py < self.margin or py > self.width-self.margin:
						continue

					# Multiply by cos of angle to get a straight line
					if dst > self.radius*np.cos(ang):
						continue

					detected = dst,ang,px,py
					break

				#print(f"x={x:.2f} y={y:.2f} tht={np.degrees(theta):.2f}")
				if detected is not None:
					self.detected_func(*detected)
					has_detected = True
				else:
					if has_detected and self.cleared_func is not None:
						self.cleared_func()
					has_detected = False
				time.sleep(0.025)
			except Exception as e:
				print(f"Lidar thread Exception: {e}")

class DisplayHandler:
	def __init__(self, addr=LCD_ADDR, cols=LCD_COLS, rows=LCD_ROWS, rate=10, asserv=None, action=None, jumper=None, debug=False, thread=True):
		self.rate = rate
		self.asserv = asserv
		self.action = action
		self.jumper = jumper
		self.debug = debug
		self.use_thread = thread
		self.score = 0

		# Init. LCD
		self.disp = CharLCD(i2c_expander='PCF8574', address=addr, port=1, cols=cols, rows=rows)
		self.disp.clear()

		self.thread = None
		self.alive = False

	def start(self):
		if not self.use_thread:
			self.draw_display()
			return
		self.alive = True
		self.thread = threading.Thread(target=self.thread_func, daemon=True)
		self.thread.start()

	def stop(self):
		if not self.use_thread:
			return
		self.alive = False
		self.thread.join()
		self.thread = None

	def set_score(self, score):
		self.score = score
		if not self.use_thread:
			self.draw_display()

	def add_score(self, val):
		self.set_score(self.score + val)

	def clear_score(self):
		self.set_score(0)

	def get_score(self):
		return self.score

	def draw_display(self):
		if self.debug:
			if self.asserv is not None:
				dst, theta = self.asserv.get_pos()
				x,y = self.asserv.get_pos_xy()
				theta %= (1 if theta >= 0 else -1)*2*np.pi

				linest = f"{int(x)}"
				linest = linest.ljust(6)
				linest += f"{int(y)}"
				linest = linest.ljust(6*2)
				linest += f"{int(np.degrees(theta))}"
				linest = linest.ljust(20)
				self.disp.cursor_pos = (0, 0)
				self.disp.write_string(linest)

			linest = ""

			if self.asserv is not None:
				run = self.asserv.running
				state = self.asserv.debug_get_controller_state()
				if run:
					if state == 0:
						linest += "THETA"
					elif state == 1:
						linest += "DST"
					else:
						linest += "REACH"
				else:
					linest += "OFF"

			if self.jumper is not None:
				linest = linest.ljust(6)
				if self.jumper.state():
					linest += "IN"
				else:
					linest += "OUT"

			if self.action is not None:
				linest = linest.ljust(10)
				rd, ld = self.action.right_arm_deployed(), self.action.left_arm_deployed()
				if ld:
					linest += "DEP"
				else:
					linest += "FLD"
				linest = linest.ljust(14)

				if rd:
					linest += "DEP"
				else:
					linest += "FLD"

			if self.action is not None or self.asserv is not None or self.jumper is not None:
				linest = linest.ljust(20)
				self.disp.cursor_pos = (1, 0)
				self.disp.write_string(linest)

			if self.asserv is not None:
				lvel, lcurr, ltemp, lvbus = self.asserv.debug_get_left_bg_stats()
				rvel, rcurr, rtemp, rvbus = self.asserv.debug_get_right_bg_stats()
				linest = f"{int(ltemp)}C"
				linest = linest.ljust(5)
				linest += f"{lcurr:.1f}A"
				linest = linest.ljust(10)
				linest += f"{rcurr:.1f}A"
				linest = linest.ljust(15)
				linest += f"{int(rtemp)}C"
				linest = linest.ljust(20)

				self.disp.cursor_pos = (2, 0)
				self.disp.write_string(linest)

		self.disp.cursor_pos = (3, 0)
		self.disp.write_string(f"     Score: {self.score}".ljust(20))

	def thread_func(self):
		while self.alive:
			self.draw_display()
			time.sleep(1/self.rate)

class HCSR04Handler:
	def __init__(self, trig, echo, width, length, max_dst, margin, pos_func, detected_func, cleared_func=None, dir=1):
		self.sensor = sensor.Measurement(trig, echo)
		self.max_dst = max_dst
		self.pos_func = pos_func
		self.detected_func = detected_func
		self.cleared_func = cleared_func
		self.width = width
		self.length = length
		self.margin = margin
		self.dir = dir

	def thread_func(self):
		has_detected = False
		while self.alive:
			x,y,theta = self.pos_func()
			while True:
				try:
					dst = self.dir*self.sensor.raw_distance(sample_size=1, sample_wait=0.1)*10.0
					break
				except Exception:
					pass
			px = x + dst*np.cos(theta)
			py = y + dst*np.sin(theta)

			if px < self.margin or px > self.length-self.margin or py < self.margin or py > self.width-self.margin:
				continue

			if abs(dst) < self.max_dst:
				self.detected_func(dst, theta, px, py)
				has_detected = True
			else:
				if has_detected and self.cleared_func is not None:
					self.cleared_func()
				has_detected = False

	def start(self):
		self.alive = True
		self.thread = threading.Thread(target=self.thread_func, daemon=True)
		self.thread.start()

	def stop(self):
		self.alive = False
		self.thread.join()
		self.thread = None

def inst(func):
	def inner(self, *args, **kwargs):
		# Call the function normally
		func(self, *args, **kwargs)

		blocking = kwargs["blocking"] if "blocking" in kwargs else True

		if self.inst_wait != 0 and blocking:
			time.sleep(self.inst_wait)

	return inner

class BaseScenario:
	def __init__(self, asserv, start_x, start_y, start_theta, inst_wait=0, ip_nuc=None, mcom_class=None, obs_restart=False):
		self.start_x = start_x
		self.start_y = start_y
		self.start_theta = start_theta

		self.asserv = asserv
		self.inst_wait = inst_wait
		self.obs_restart = obs_restart

		self.start_info = mqtt.InfoDebut()
		self.mcom = None
		if ip_nuc is not None and mcom_class is not None:
			objs = [self.start_info]
			objs.extend(self.get_mcom_objs())
			self.mcom = mcom_class(ip_nuc, objs)

		self.started = False

		if self.mcom is not None:
			self.mcom.demarre_fil()

		self.stop_thread = threading.Thread(target=self.stop_thread_func, daemon=True)
		self.stop_thread.start()

	def stop_thread_func(self):
		while not self.started:
			time.sleep(0.01)
		time.sleep(MATCH_PLAY_TIME)
		self.finish()

	# dst in mm, angle in deg
	@inst
	def move(self, dst, angle=0, **kwargs):
		self.asserv.move(dst, np.radians(angle), **kwargs)

	# angle in deg
	@inst
	def turn(self, angle, **kwargs):
		self.asserv.move(0, np.radians(angle), **kwargs)

	# Table coords ? maybe
	@inst
	def move_abs(self, x, y, **kwargs):
		self.asserv.move_abs(x, y, **kwargs)

	def get_rel_pos(self):
		_, theta = self.asserv.get_pos()
		x,y = self.asserv.get_pos_xy()
		return x,y,theta

	def get_pos(self, x_off=0, y_off=0):
		x_rel,y_rel, theta_rel = self.get_rel_pos()

		# Rotate the x and y axis to the start angle
		# to bring it back to the table ref.
		cos_tht_st = np.cos(self.start_theta)
		sin_tht_st = np.sin(self.start_theta)
		x_rel_table = cos_tht_st*x_rel - sin_tht_st*y_rel
		y_rel_table = sin_tht_st*x_rel + cos_tht_st*y_rel

		# Project the offset in the table
		theta = theta_rel+self.start_theta
		cos_tht = np.cos(theta)
		sin_tht = np.sin(theta)
		x_off_table = cos_tht*x_off - sin_tht*y_off
		y_off_table = sin_tht*x_off + cos_tht*y_off

		# Add everything
		x = self.start_x + x_rel_table + x_off_table
		y = self.start_y + y_rel_table + y_off_table

		return x,y,theta

	def obs_detect(self, dst, theta, x, y):
		print(f"Obs x={x}, y={y}, dst={dst} theta(deg)={np.degrees(theta)}")
		if self.started:
			self.asserv.notify_stop()

	def obs_cleared(self):
		if self.started and self.obs_restart:
			self.asserv.notify_stop_clear()

	def run(self):
		try:
			self.startup()

			self.started = True
			self.play()
			self.started = False
		finally:
			self.finish()

	# ====== To implement =======

	# Inits once, should store objects in instance
	def get_mcom_objs(self):
		return []

	def play(self):
		raise NotImplementedError("Scenario needs a play method")

	# Happens before the play, needs to wait for the right time here, either using a jumper or with mcom
	def startup(self):
		self.asserv.start()

	# When you play returns, be called after 100s regardless
	def finish(self):
		print("Stopping everything")
		self.asserv.stop()

class Scenario(BaseScenario):
	def __init__(self, asserv, action, start_x, start_y, start_theta, inst_wait=0, jumper_safe=True, lidar_enable=True, lidar_restart=False, lidar_radius=300, lidar_margin=10, ip_nuc=None):
		super().__init__(asserv, start_x, start_y, start_theta, inst_wait, ip_nuc, mqtt.Poulet, lidar_restart)
		self.action = action

		self.jumper = JumperStart(safe=jumper_safe)
		self.lidar = LidarHandler(TABLE_WIDTH, TABLE_LENGTH, lidar_radius, lidar_margin, lambda: self.get_pos(LIDAR_OFFSET_TO_FRONT - ENCODER_OFFSET_TO_FRONT),
								self.obs_detect, self.obs_cleared) if lidar_enable else None
		self.disp = DisplayHandler(asserv=self.asserv, action=self.action, jumper=self.jumper, thread=False)

	@inst
	def arm_deploy(self, left, deploy, half=False, **kwargs):
		if left:
			if deploy:
				if half:
					self.action.left_arm_half_deploy(**kwargs)
				else:
					self.action.left_arm_deploy(**kwargs)
			else:
				self.action.left_arm_fold(**kwargs)
		else:
			if deploy:
				if half:
					self.action.right_arm_half_deploy(**kwargs)
				else:
					self.action.right_arm_deploy(**kwargs)
			else:
				self.action.right_arm_fold(**kwargs)

	# ammount in deg
	@inst
	def arm_turn(self, left, ammount, **kwargs):
		if left:
			self.action.left_arm_turn(ammount, **kwargs)
		else:
			self.action.right_arm_turn(ammount, **kwargs)

	def set_score(self, score):
		self.disp.set_score(score)

	def add_score(self, val):
		self.disp.add_score(val)

	def clear_score(self):
		self.disp.clear_score()

	def startup(self):
		super().startup()
		self.action.start()

		self.action.right_arm_fold()
		self.action.left_arm_fold()

		if self.lidar is not None:
			print("Starting LIDAR...")
			self.lidar.start()
			print("LIDAR up.")

		self.disp.start()

		self.jumper.wait()
		self.start_info.demarrer()

	def finish(self):
		super().finish()
		self.action.stop()

	def play(self):
		raise NotImplementedError("Scenario needs a play method")


class PaminableScenario(BaseScenario):
	def __init__(self, asserv, start_x, start_y, start_theta, inst_wait=0, ultra_enable=True, ultra_restart=False, ultra_radius=300, ultra_margin=10, ip_nuc=None):
		super().__init__(asserv, start_x, start_y, start_theta, inst_wait, ip_nuc, mqtt.Paminable, ultra_restart)

		self.ultra = HCSR04Handler(HCSR04_TRIG, HCSR04_ECHO, TABLE_WIDTH, TABLE_LENGTH, ultra_radius, ultra_margin, lambda: self.get_pos(HCSR04_OFFSET_TO_ENCODER),
								self.obs_detect, self.obs_cleared, -1) if ultra_enable else None

	def startup(self):
		super().startup()
		if self.ultra is not None:
			print("Starting HC-SR04...")
			self.ultra.start()

		if self.mcom is not None:
			self.start_info.attends()
