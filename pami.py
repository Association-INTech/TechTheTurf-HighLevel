import time, math, socket
import comm

INST_WAIT = 0
BLUE_SIDE = True

pico = comm.make_asserv()
pico.start()

print("Started...")

HOST = ""
PORT = 13377

try:
	
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((HOST, PORT))
		s.listen()
		conn, addr = s.accept()

	pico.move(1700,0)
	time.sleep(INST_WAIT)
	pico.move(0,math.radians(-80 if BLUE_SIDE else 100))
	time.sleep(INST_WAIT)
	pico.move(1000,0)
	time.sleep(INST_WAIT)
finally:
	pico.stop()