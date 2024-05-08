import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
import numpy as np
import matplotlib, pathlib, time

# Faster live plot
matplotlib.use('Qt5Agg')

TABLE_WIDTH = 2000
TABLE_LENGTH = 3000

class Robot:
	def __init__(self, width, height, rotationx_offset=0, color="#0000FF"):
		self.width = width
		self.length = height
		self.rotationx_offset = rotationx_offset
		self.x = 0
		self.y = 0
		self.theta = 0
		self.color = color

		self.patch_rect = None
		self.patch_xarrow = None
		self.patch_yarrow = None

	@classmethod
	def create_main(cls, initalx, initaly, initaltheta=0):
		inst = cls(350, 200, (200/2)-145, "#3434C6")
		inst.x = initalx
		inst.y = initaly
		inst.theta = initaltheta
		return inst

	@classmethod
	def create_pami(cls, initalx, initaly, initaltheta=0):
		inst = cls(150, 150, 0, "#F5FF54")
		inst.x = initalx
		inst.y = initaly
		inst.theta = initaltheta
		return inst

	def update_pos(self, x, y, theta):
		self.x = x
		self.y = y
		self.theta = theta

	def get_angle(self):
		return np.pi/2+self.theta

	def _calc_xy_rect(self):
		return (self.x-self.width/2, self.y-self.length/2)

	def _calc_dx_arrow(self, angle_offset=0):
		return (self.length/3)*np.cos(self.get_angle()-(np.pi/2)+angle_offset)

	def _calc_dy_arrow(self, angle_offset=0):
		return (self.length/3)*np.sin(self.get_angle()-(np.pi/2)+angle_offset)

	def bind(self, axis):
		self.patch_rect = patches.Rectangle(self._calc_xy_rect(), self.width, self.length,
							angle=np.degrees(self.get_angle()), rotation_point="center", fill=True, edgecolor="black", facecolor=self.color)
		self.patch_xarrow = patches.FancyArrow(self.x, self.y, self._calc_dx_arrow(), self._calc_dy_arrow(), color="red", width=self.length/40)
		self.patch_yarrow = patches.FancyArrow(self.x, self.y, self._calc_dx_arrow(np.pi/2), self._calc_dy_arrow(np.pi/2), color="lime", width=self.length/40)
		axis.add_patch(self.patch_rect)
		axis.add_patch(self.patch_xarrow)
		axis.add_patch(self.patch_yarrow)

	def update_patch(self):
		self.patch_rect.set_angle(np.degrees(self.get_angle()))
		self.patch_rect.set_xy(self._calc_xy_rect())
		self.patch_xarrow.set_data(x=self.x, y=self.y, dx=self._calc_dx_arrow(), dy=self._calc_dy_arrow())
		self.patch_yarrow.set_data(x=self.x, y=self.y, dx=self._calc_dx_arrow(np.pi/2), dy=self._calc_dy_arrow(np.pi/2))
		return self.patch_rect, self.patch_xarrow, self.patch_yarrow

class Visualiser:
	def __init__(self, robot, pamis=[], fps=60, on_click=None):
		self.fps = fps
		self.fig, self.ax = plt.subplots()
		self.plants = np.array([])
		self.robot = robot
		self.pamis = pamis
		self.plant_scatter = None

		self.on_click = on_click
		self.fig.canvas.mpl_connect("button_press_event", self._on_click)

	def _on_click(self, event):
		if self.on_click is not None:
			self.on_click(event)

	def update_func(self, frame):
		plots = [self.plant_scatter]
		self.robot.theta = time.time()
		self.plant_scatter.set_offsets(self.plants)
		plots.extend(self.robot.update_patch())
		for pami in self.pamis:
			plots.extend(pami.update_patch())
		return plots

	def start(self):
		impath = pathlib.Path(__file__).parent.resolve()/"table.png"
		img = plt.imread(impath)

		self.fig.set_layout_engine("tight")
		self.ax.imshow(img, extent=[0, TABLE_LENGTH, 0, TABLE_WIDTH], alpha=0.6)
		self.plant_scatter = self.ax.scatter(self.plants.T[0], self.plants.T[1], s=50, c="green")
		self.robot.bind(self.ax)
		for pami in self.pamis:
			pami.bind(self.ax)
		self.anim = animation.FuncAnimation(fig=self.fig, func=self.update_func, interval=1/self.fps, blit=True)
		plt.show()


if __name__ == "__main__":
	main = Robot.create_main(500, 500, np.radians(65))
	pamis = [Robot.create_pami(100,100), Robot.create_pami(200,200)]
	vis = Visualiser(main, pamis)
	vis.plants = np.array([[1000, 1000], [1500, 1000]])
	vis.start()