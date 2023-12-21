import robot
import smbus2

# Definition of Picos

ASSERV_I2C_ADDR = 0x69
ACTS_I2C_ADDR = 0x42

I2C_BUS = smbus2.SMBus(1)

def makeAsserv():
	return robot.Asserv(I2C_BUS, ASSERV_I2C_ADDR)

#def makeActs():
#	return robot.Acts(I2C_BUS, ACTS_I2C_ADDR)
