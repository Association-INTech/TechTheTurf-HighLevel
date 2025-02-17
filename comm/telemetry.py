from dataclasses import dataclass
import threading
import socket
import struct
import zlib

ENDIANNESS = "<"

UPLINK_HEADER = b"\xDE\xAD"

@dataclass
class TelemetryPacketBase:
	timestamp: float

	def vals(self):
		vals = self.__dict__.copy()
		del vals["timestamp"]
		return vals

	@staticmethod
	def fmt():
		return ENDIANNESS+"f"

@dataclass
class PidTelemetryPacket(TelemetryPacketBase):
	target: float
	input: float
	output: float

	@staticmethod
	def fmt():
		return "fff"

@dataclass
class PowerTelemetryPacket(TelemetryPacketBase):
	voltage: float
	current: float
	power: float

	@staticmethod
	def fmt():
		return "fff"

TELEMETRY_TYPES = {0: PidTelemetryPacket, 1: PowerTelemetryPacket}

@dataclass
class Telemetry:
	name: str
	idx: int
	packet_type: TelemetryPacketBase
	fmt: str = ""
	size: int = 0

	def __init__(self, name, idx, packet_base):
		self.name = name
		self.idx = idx
		self.packet_type = packet_base
		self.fmt = Telemetry.get_format(packet_base)
		self.size = struct.calcsize(self.fmt)

	def get_format(ty):
		if "fmt" not in ty.__dict__:
			return None
		st = ""
		for base in ty.__bases__:
			if "fmt" not in base.__dict__:
				continue
			st += Telemetry.get_format(base)
		return st + ty.fmt()

	def to_packet(self, data):
		return self.packet_type(*struct.unpack(self.fmt,data))

	def to_bytes(self, packet):
		return struct.pack(self.fmt, *packet.__dict__.values())

	def fields(self):
		vals = self.packet_type.__dict__["__match_args__"]
		return tuple(filter(lambda x:x!="timestamp", vals))

class Client:
	def __init__(self, addr, port, callback):
		self.alive = True
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((addr, port))

		self.callback = callback

		self.client_thread = threading.Thread(target=self.client_handler, daemon=True)
		self.client_thread.start()

	def stop(self):
		self.sock.close()
		self.alive = False
		self.client_thread.join()

	def client_handler(self):
		while self.alive:
			try:
				dat = self.sock.recv(1)
				if dat is None:
					break
				if struct.unpack(ENDIANNESS + "B",dat)[0] != UPLINK_HEADER[0]:
					continue
				#print(dat)

				dat = self.sock.recv(1)
				if dat is None:
					break

				if struct.unpack(ENDIANNESS + "B",dat)[0] != UPLINK_HEADER[1]:
					continue
			except Exception as e:
				print(e)
				break

			try:
				size_dat = self.sock.recv(2)
				if size_dat is None:
					break
			except:
				break

			if len(size_dat) < 2:
				continue

			size, idx = struct.unpack(ENDIANNESS + "BB", size_dat)

			try:
				pkt_data = self.sock.recv(size)
				if pkt_data is None:
					break
			except:
				break

			try:
				dat = self.sock.recv(4)
				if dat is None:
					break

				crc, = struct.unpack(ENDIANNESS + "I", dat)
				calc = zlib.crc32(size_dat+pkt_data)

				if crc != calc:
					#print("CRC mismatch")
					continue
			except Exception as e:
				continue

			self.callback(idx, pkt_data)

		self.alive = False