import time
import math
import comm

# Example scenario

asserv = comm.make_asserv()

asserv.start()

side_len = 500 # mm

for i in range(4):
	print(i)
	asserv.move(side_len, 0)
	time.sleep(2)
	asserv.move(0, math.radians(90))
	time.sleep(2)

asserv.stop()