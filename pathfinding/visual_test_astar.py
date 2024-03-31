from working_a_star import BinaryGridGraph, shortest_path
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

TYPES = VOID, OBSTACLE, PATHWAY, VISITED = range(4)

colors = [
    (.5, .5, .5),
    (0, 0, 0),
    (1., 0, 0),
    (.5, 0, 0),
    *[(1., 1., 1.)] * (256 - len(TYPES))
]
CMAP = ListedColormap(colors, 'Xx_Cmap0_xX')


def test_random_obstacles(nb_test=5):
    w, h = 400, 400
    for _ in range(nb_test):
        grid = np.zeros((w, h), np.uint8)

        x, y = np.mgrid[:w, :h]
        for _ in range(30):
            cx, cy = random.random() * w, random.random() * h
            rad = (1 + 2 * random.random()) * (w * w + h * h) ** .5 / 40
            grid[:] |= (x - cx) ** 2 + (y - cy) ** 2 < rad * rad
        grid[0, 0] = 0

        graph = BinaryGridGraph(grid)
        path, costs = shortest_path(graph, (0, 0), (w-1, h-1))
        path = np.array(path)

        fig: plt.Figure
        ax: plt.Axes
        fig, ax = plt.subplots(figsize=(10, 10))

        img = grid.copy()
        img[costs != -1] = VISITED
        img[path[:, 0], path[:, 1]] = PATHWAY
        ax.matshow(img, cmap=CMAP, vmin=0, vmax=255)

        ax.set_axis_off()
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.show()


if __name__ == '__main__':
    # For reproducibility
    random.seed(10)
    test_random_obstacles()
    # plot_examples([CMAP])