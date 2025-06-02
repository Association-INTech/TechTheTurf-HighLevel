import time, math, sys
import handlers, comm
import comm.robot

#NUC_IP = "192.168.8.125"
NUC_IP = None

INST_WAIT = 0
BLUE_SIDE = sys.argv[1] == "b"

START_X = handlers.TABLE_LENGTH + ((-(53.75/2.0)-1.0)) if BLUE_SIDE else (53.75/2.0)+1.0
START_Y = handlers.TABLE_WIDTH - 100.0
START_THETA = math.radians(180) if BLUE_SIDE else 0

SIDE_DIR = 1 if BLUE_SIDE else -1

JUMPER_SAFE = False
TOF_ENABLE = True
TOF_RESTART = True
TOF_DST = 200.0
TOF_MARGIN = 10.0

class CustomScenario(handlers.PaminiScenario):
	def startup(self):
		self.asserv.debug_set_effects(comm.robot.ControlState.AUTOMATIC)
		super().startup()

	def play(self):
		time.sleep(86)
		self.move(1300-50)
		self.turn(90*SIDE_DIR)
		self.move(300)
		self.asserv.debug_set_effects(comm.robot.ControlState.SHOW)

print(f"Running {'Blue' if BLUE_SIDE else 'Yellow'} side scenario.")
asserv = comm.make_asserv()
scenar = CustomScenario(asserv, START_X, START_Y, START_THETA, INST_WAIT,
					TOF_ENABLE, TOF_RESTART, TOF_DST, TOF_MARGIN, NUC_IP, JUMPER_SAFE)
scenar.run()