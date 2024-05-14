import time, math, socket
import handlers
import comm

"""
Scénario alternatif v1 : voir image/main2.png
"""
# ======== Settings ========

# :)
LIDAR_ENABLE = True
# Side
BLUE_SIDE = False 
# Only run on negative edge of jumper switch
JUMPER_SAFE = False
# Continues after the obstacle is no more
RESTART_AFTER_OBS_CLEAR = False
# Pretty self explanatory
LIDAR_DETECT_RADIUS = 450
# Only check with table bounds - margin for lidar
LIDAR_TABLE_MARGIN = 10
# Offset to the border of the table
BORDER_SETUP_OFFSET = 35
# Time to wait between commands
INST_WAIT = 0.3

# ===========================

# We start off at the bottom left or right corner of the table facing forwards
# So the X is unchanged but Y is flipped when we are on the bottom right, so Yellow team
SIDE_DIR = 1 if BLUE_SIDE else -1

START_X = SIDE_DIR * (handlers.ROBOT_WIDTH - handlers.ENCODER_OFFSET_TO_FRONT) + (
    0 if BLUE_SIDE else handlers.TABLE_LENGTH)
START_Y = BORDER_SETUP_OFFSET + handlers.ROBOT_LENGTH / 2.0
START_THETA = 0 if BLUE_SIDE else math.radians(180)


# Example scenario

class CustomScenario(handlers.Scenario):
    def play(self):
        st = time.time()
        #self.move(275-(ROBOT_LENGTH-ARM_OFFSET_TO_FRONT), 0)
        self.move(215)
        for i in range(3):
            self.arm_deploy(not BLUE_SIDE, True)
            self.arm_turn(not BLUE_SIDE, SIDE_DIR * 90)
            self.add_score(5)
            self.arm_deploy(not BLUE_SIDE, False, blocking=False)

            if i != 2:
                self.move(220)

        self.move(550)

        for i in range(3):
            self.arm_deploy(not BLUE_SIDE, True)
            self.arm_turn(not BLUE_SIDE, SIDE_DIR * 90)
            self.add_score(5)
            self.arm_deploy(not BLUE_SIDE, False, blocking=False)

            if i != 2:
                self.move(220)

        self.move(250)
        self.move(-250)
        self.turn(SIDE_DIR * 60)
        self.move(855)

        self.turn(SIDE_DIR * (-60))

        self.move(550)
        self.asserv.stop()
        self.add_score(10)

print(f"Running {'Blue' if BLUE_SIDE else 'Yellow'} side scenario.")
asserv = comm.make_asserv()
action = comm.make_action()
scenar = CustomScenario(asserv, action, START_X, START_Y, START_THETA, INST_WAIT, JUMPER_SAFE,
                        LIDAR_ENABLE, RESTART_AFTER_OBS_CLEAR, LIDAR_DETECT_RADIUS, LIDAR_TABLE_MARGIN)

scenar.run()



