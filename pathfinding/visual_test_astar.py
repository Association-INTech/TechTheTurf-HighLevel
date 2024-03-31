from working_a_star import BinaryGridGraph, shortest_path, shortest_path_no_heap_optimization
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import time

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
            # put obstacles
            cx, cy = random.random() * w, random.random() * h
            rad = (1 + 2 * random.random()) * (w * w + h * h) ** .5 / 40
            grid[:] |= (x - cx) ** 2 + (y - cy) ** 2 < rad * rad
        grid[0, 0] = VOID

        graph = BinaryGridGraph(grid)
        date = time.perf_counter()
        path, costs = shortest_path(graph, (0, 0), (w-1, h-1))
        optimized_time = time.perf_counter() - date

        date = time.perf_counter()
        shortest_path_no_heap_optimization(graph, (0, 0), (w-1, h-1))
        terrible_time = time.perf_counter() - date
        path = np.array(path)

        fig: plt.Figure
        ax: plt.Axes
        fig, ax = plt.subplots(figsize=(10, 10))

        img = grid.copy()
        # Mark visited node in dark red
        img[costs != -1] = VISITED
        # Mark the path in red
        img[path[:, 0], path[:, 1]] = PATHWAY
        ax.matshow(img, cmap=CMAP, vmin=0, vmax=255)

        # remove axes
        ax.set_axis_off()
        # remove white space
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        print(f'Default time: {terrible_time:.03f} s, Optimized time: {optimized_time:.03f} s')
        plt.show()


if __name__ == '__main__':
    # For reproducibility
    random.seed(b'BLUE')
    test_random_obstacles()