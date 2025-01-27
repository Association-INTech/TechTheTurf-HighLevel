from .robot import Asserv, Action

NO_SMBUS = False

# Check if we're running on the raspi
try:
	import smbus2
except Exception:
	print("Running without SMBUS")
	NO_SMBUS = True

# Definition of Picos

ASSERV_I2C_ADDR = 0x69
ACTION_I2C_ADDR = 0x68

I2C_BUS = None if NO_SMBUS else smbus2.SMBus(1)

def make_asserv():
	return Asserv(I2C_BUS, ASSERV_I2C_ADDR)

def make_action():
	return Action(I2C_BUS, ACTION_I2C_ADDR)
