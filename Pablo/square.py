import time
import math
import sys
import robots

# Example scenario

asserv = robots.makeAsserv()

asserv.start()

side_len = float(sys.argv[1])

for i in range(4):
	asserv.move(side_len, 0)
	time.sleep(2)
	asserv.move(0, math.radians(90))
	time.sleep(2)

asserv.stop()