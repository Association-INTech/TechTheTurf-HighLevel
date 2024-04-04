from min_heap_binary_tree import MinHeapBinaryTree
from a_star import AStar
from matplotlib import pyplot as plt
import numpy as np

# tree stuff.
tree = MinHeapBinaryTree(lambda i: i, np.array([-1 for _ in range(20)]))

tree.push(10)
tree.push(3)
tree.push(15)
tree.push(1)
tree.push(4)

# A star stuff.

X_SIZE = 100
Y_SIZE = 100

astar = AStar(X_SIZE, Y_SIZE)

for y in range(60):
    astar.update_grid(50, y, 1)

start_index = astar.pos_to_index(0, 0)
end_index = astar.pos_to_index(99, 30)

path = astar.find_path(start_index, end_index)
if path is None:
    print("None")
else:
    print(path)

image = np.array([[[astar.grid[x + y * X_SIZE] * 255, 0, 0] for x in range(X_SIZE)] for y in range(Y_SIZE)], dtype=int)

for path_point in path:
    x, y = astar.index_to_pos(path_point)
    image[y][x] = [255, 255, 255]

x, y = astar.index_to_pos(start_index)
image[y][x] = [0, 255, 0]
x, y = astar.index_to_pos(end_index)
image[y][x] = [255, 0, 0]

plt.imshow(image)
plt.show()
