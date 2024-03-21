from min_heap_binary_tree import MinHeapBinaryTree, Comparison
from a_star import AStar

# tree stuff.
tree = MinHeapBinaryTree(lambda i, j: Comparison.from_int(i, j))

tree.push(10)
tree.push(3)
tree.push(15)
tree.push(1)
tree.push(4)
tree.push(4)

tree.pop()

# A star stuff.

astar = AStar(10, 10)

path = astar.find_path(0, 99)
if path is None:
    print("None")
print(path)
