import sys
import telemetry
import robot
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

robot = robot.Asserv()

class TelemetryPlot:
	def __init__(self, telem):
		self.telem = telem
		pretty_name = telem.name.replace("_"," ").capitalize()
		self.fig = plt.figure(pretty_name)
		self.ax = self.fig.gca()
		self.ax.set_ylim(-100,100)
		self.ax.set_title(pretty_name)
		self.ax.set_xlabel("Time (s)")
		self.plots = {name:self.ax.plot([], [], label=name)[0] for name in telem.fields()}
		self.time_data = []
		self.plot_data = {name:[] for name in telem.fields()}
		self.fig.legend()
		self.anim = FuncAnimation(self.fig, self.update, interval=16, blit=True)

	def update(self, i):
		for name in self.plots.keys():
			self.plots[name].set_data(self.time_data, self.plot_data[name])

		if len(self.time_data) > 0:
			mval = self.time_data[-1]
			self.ax.set_xlim(mval-10.0, mval)

		return self.plots.values()

	def handle_data(self, dat):
		pkt = self.telem.to_packet(dat)
		ts = pkt.timestamp

		if ts == 0:
			self.time_data = []
			for name in self.plot_data.keys():
				self.plot_data[name] = []

		self.time_data.append(ts)
		for name, val in pkt.vals().items():
			self.plot_data[name].append(val)

plots = {}
for idx, telem in robot.telems.items():
	plots[idx] = TelemetryPlot(telem)

def cb_func(idx, dat):
	plots[idx].handle_data(dat)

if len(sys.argv) < 2:
	print("Give IP")
	exit()

cl = telemetry.Client(sys.argv[1], 1337, cb_func)

plt.show()