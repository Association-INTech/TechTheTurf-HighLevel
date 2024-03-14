import time
import math

import comm

# Example scenario

asserv = comm.make_asserv()

asserv.set_telem(asserv.telem_from_idx(0), True)
asserv.set_telem(asserv.telem_from_idx(1), True)
asserv.set_telem(asserv.telem_from_idx(2), True)
asserv.set_telem(asserv.telem_from_idx(3), True)

asserv.start()

side_len = 500 # mm

print("move")
asserv.move(1000, 0, blocking=False)
time.sleep(1)
print("estop")
asserv.emergency_stop()
time.sleep(1)
print("balls")

"""
for i in range(4):
	print(i)
	asserv.move(side_len, 0)
	time.sleep(2)
	asserv.move(0, math.radians(90))
	time.sleep(2)
"""

asserv.stop()