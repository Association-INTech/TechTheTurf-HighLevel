import time, math
import handlers, comm

NUC_IP = None

INST_WAIT = 0
BLUE_SIDE = False

START_X = handlers.TABLE_LENGTH + (-450.0/2.0 if BLUE_SIDE else 450/2.0)
START_Y = handlers.TABLE_WIDTH - handlers.PAMINABLE_ENCODER_OFFSET_TO_FRONT
START_THETA = math.radians(90)

ULTRA_ENABLE = True
ULTRA_RESTART = False
ULTRA_DST = 300.0
ULTRA_MARGIN = 10.0

class CustomScenario(handlers.PaminableScenario):
	def play(self):
		#time.sleep(90.0)
		self.move(-1700)
		self.turn(80 if BLUE_SIDE else -100)
		self.move(-1000)

print(f"Running {'Blue' if BLUE_SIDE else 'Yellow'} side scenario.")
asserv = comm.make_asserv()
scenar = CustomScenario(asserv, START_X, START_Y, START_THETA, INST_WAIT,
					ULTRA_ENABLE, ULTRA_RESTART, ULTRA_DST, ULTRA_MARGIN, NUC_IP)
scenar.run()