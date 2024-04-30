import time, math
import handlers
import comm

# ======== Settings ========

# :)
LIDAR_ENABLE = True
# Side
BLUE_SIDE = True
# Only run on negative edge of jumper switch
JUMPER_SAFE = True
# Continues after the obstacle is no more
RESTART_AFTER_OBS_CLEAR = False
# Pretty self explanatory
LIDAR_DETECT_RADIUS = 250
# Offset to the border of the table
BORDER_SETUP_OFFSET = 30
# Time to wait between commands
INST_WAIT = 0

# ===========================

# We start off at the bottom left or right corner of the table facing forwards
# So the X is unchanged but Y is flipped when we are on the bottom right, so Yellow team
SIDE_DIR = 1 if BLUE_SIDE else -1

START_X = SIDE_DIR*(handlers.ROBOT_WIDTH - handlers.ENCODER_OFFSET_TO_FRONT) + (0 if BLUE_SIDE else handlers.TABLE_LENGTH)
START_Y = BORDER_SETUP_OFFSET + handlers.ROBOT_LENGTH/2.0
START_THETA = 0 if BLUE_SIDE else math.radians(180)

# Example scenario

class CustomScenario(handlers.Scenario):
	def play(self):
		#self.move(275-(ROBOT_LENGTH-ARM_OFFSET_TO_FRONT), 0)
		self.move(215)
		for i in range(3):
			self.arm_deploy(not BLUE_SIDE, True)
			self.arm_turn(not BLUE_SIDE, SIDE_DIR*90)
			self.add_score(5)
			self.arm_deploy(not BLUE_SIDE, False)

			if i != 2:
				self.move(220)

		self.turn(SIDE_DIR*90)
		self.move(handlers.ROBOT_WIDTH+325*2+450+155)
		self.turn(SIDE_DIR*90)
		self.move(225*2+75, 0)
		self.add_score(10)
		time.sleep(10)
		#time.sleep(5)
		"""
		self.move(0, math.radians(SIDE_DIR*90))
		self.move(400-BORDER_SETUP_OFFSET-ROBOT_WIDTH, 0)
		self.move(0, math.radians(-SIDE_DIR*90))
		self.move(500, 0)
		self.move(0, math.radians(SIDE_DIR*90))
		self.move(600, 0)
		self.move_abs(asserv, 0, 0)
		"""
		#dst, theta = asserv.get_pos()
		#self.move(-dst+40, 0)

		#left = MATCH_PLAY_TIME - (time.time()-start_time)
		#print(f"Finished, let's chill until the end, {left:.2f}s left")
		#time.sleep(left)

print(f"Running {'Blue' if BLUE_SIDE else 'Yellow'} side scenario.")
asserv = comm.make_asserv()
action = comm.make_action()
scenar = CustomScenario(asserv, action, START_X, START_Y, START_THETA, INST_WAIT, JUMPER_SAFE,
					LIDAR_ENABLE, RESTART_AFTER_OBS_CLEAR, LIDAR_DETECT_RADIUS)

scenar.run()