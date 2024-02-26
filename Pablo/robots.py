import robot
import smbus2

# Definition of Picos

ASSERV_I2C_ADDR = 0x69
ACTION_I2C_ADDR = 0x68

I2C_BUS = smbus2.SMBus(1)

def makeAsserv():
	return robot.Asserv(I2C_BUS, ASSERV_I2C_ADDR)

def makeAction():
	return robot.Action(I2C_BUS, ACTION_I2C_ADDR)
