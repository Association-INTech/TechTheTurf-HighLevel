import time
import robots

# Example scenario

asserv = robots.makeAsserv()

asserv.start()

asserv.wait_completed()

for i in range(4):
	asserv.move(side_len, 0)
	time.sleep(2)
	asserv.move(0, math.radians(90))
	time.sleep(2)
	asserv.wait_completed()

asserv.stop()