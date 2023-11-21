import serial as ser
import struct

import serial.tools.list_ports
baud = 9600
listport= ser.tools.list_ports.comports(include_links=False)

print(len(listport))
print(struct.unpack('f',ser.Serial(listport[2].device,baud,timeout=1).readline()))