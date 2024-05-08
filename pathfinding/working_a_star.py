"""
Bold name, I know; Shame on me if it does not work (works on my machine)
"""


import numpy as np
import os
from ctypes import CDLL, POINTER, c_uint32, c_uint8
import platform

DIR = os.path.dirname(__file__)

if platform.system() == 'Windows':
    c_astar = CDLL(os.path.join(DIR, 'libAstar.dll')).grid_astar
else:
    if not os.path.exists(os.path.join(DIR, 'libAstar.so')):
        print('Astar library not found, building it')
        old_dir = os.getcwd()
        os.chdir(DIR)
        os.system('sh ./build_c_astar.sh')
        os.chdir(old_dir)
        print('Astar libray built')
    c_astar = CDLL(os.path.join(DIR, 'libAstar.so')).grid_astar

c_astar.restype = POINTER(c_uint32)
MAX_UINT32 = 0xffffffff


class Graph:
    """Graph interface"""

    def get_neighbors(self, node):
        """Neighbors of a node and the cost to reach each of them"""

    def caching_array(self, dtype, fill=0) -> np.ndarray:
        """Arrays to store costs, predecessors, heuristics, etc..."""

    def hash(self, node) -> np.uint:
        """Transforms a node into an int"""

    def de_hash(self, hash_value: np.int32):
        """Reciprocal of hash"""

    # maybe not in the right place; works for me
    def heuristic(self, node, end) -> np.int32:
        return 0


class BinaryGridGraph(Graph):
    has_updated_collider_since_last_path_calculation: bool
    ONE, SQRT2 = 100, 141
    _4CONNECTED, _8CONNECTED = range(2)

    def __init__(self, grid: np.ndarray, connectivity=_8CONNECTED):
        """
        Grid 2d-array:
         - 0: walkable
         - 1: obstacle
        """
        self.width, self.height = grid.shape
        self.grid = grid
        self.has_updated_collider_since_last_path_calculation = False

        self.get_neighbors = (self.get_4_neighbors, self.get_8_neighbors)[connectivity]
        self.heuristic = (self.heuristic_4, self.heuristic_8)[connectivity]

    def get_4_neighbors(self, node):
        x, y = node
        if x and not self.grid[x-1, y]:
            yield (x-1, y), self.ONE
        if x < self.width-1 and not self.grid[x+1, y]:
            yield (x+1, y), self.ONE
        if y and not self.grid[x, y-1]:
            yield (x, y-1), self.ONE
        if y < self.height-1 and not self.grid[x, y+1]:
            yield (x, y+1), self.ONE

    def heuristic_4(self, node, end) -> np.int32:
        (x, y), (xe, ye) = node, end
        return self.ONE * (abs(x - xe) + abs(y - ye))

    def heuristic_8(self, node, end) -> np.int32:
        (x, y), (xe, ye) = node, end
        dx, dy = abs(x - xe), abs(y - ye)
        return (self.SQRT2 - self.ONE) * min(dx, dy) + self.ONE * max(dx, dy)

    def get_8_neighbors(self, node):
        yield from self.get_4_neighbors(node)
        x, y = node
        if x and y and not self.grid[x-1, y-1]:
            yield (x-1, y-1), self.SQRT2
        if x < self.width-1 and y and not self.grid[x+1, y-1]:
            yield (x+1, y-1), self.SQRT2
        if x and y < self.height-1 and not self.grid[x-1, y+1]:
            yield (x-1, y+1), self.SQRT2
        if x < self.width-1 and y < self.height-1 and not self.grid[x+1, y+1]:
            yield (x+1, y+1), self.SQRT2

    def caching_array(self, dtype, fill=0) -> np.ndarray:
        return np.full((self.width, self.height), fill, dtype)

    def hash(self, node) -> np.uint:
        x, y = node
        return y * self.width + x

    def de_hash(self, hash_value: np.int32):
        return hash_value % self.width, hash_value // self.width

    def __setitem__(self, item, value):
        if self.grid[item] != value:
            self.has_updated_collider_since_last_path_calculation = True
        self.grid[item] = value


class MinHeap(list):
    def __init__(self, index_array: np.ndarray, key):
        """
        key: function giving the value to compare with
        """
        list.__init__(self)
        self.indices = index_array
        self.key = key

    def push(self, node):
        self.indices[node] = len(self)
        self.append(node)
        self.update(node)

    def invariant(self):
        return all(self.key(self[(index - 1) // 2]) <= self.key(obj) for index, obj in enumerate(self[1:], 1))

    def index_invariant(self):
        return all(index == self.indices[value] for index, value in enumerate(self))

    def extract_min(self):
        # extract min
        result = self[0]
        self.indices[result] = -1

        if len(self) == 1:
            self.pop()
            return result

        # place last node as root
        self[0] = self.pop()
        self.indices[self[0]] = 0

        index = 0
        while 2 * index + 1 < len(self):
            minimum, min_index = self.key(self[index]), index
            left, right = 2 * index + 1, 2 * index + 2
            if left < len(self) and self.key(self[left]) < minimum:
                minimum, min_index = self.key(self[left]), left
            if right < len(self) and self.key(self[right]) < minimum:
                min_index = right

            # index is the min, no need go further down
            if min_index == index:
                break

            # exchange in the heap
            self[index], self[min_index] = self[min_index], self[index]
            # exchange in indices
            self.indices[self[index]], self.indices[self[min_index]] = index, min_index
            index = min_index

        return result

    def update(self, node):
        index, key = self.indices[node], self.key(node)
        parent_index = (index - 1) // 2
        while index >= 1 and key < self.key(self[parent_index]):
            # exchange in the heap
            self[index], self[parent_index] = self[parent_index], self[index]
            # exchange in indices
            self.indices[node], self.indices[self[index]] = parent_index, index
            index, parent_index = parent_index, (parent_index - 1) // 2


def shortest_path(graph: Graph, start, end) -> tuple[list, np.ndarray]:
    """
    A* shortest path algorithm

    return path (and costs for visual debug purposes)
    """
    costs, heuristics, predecessors = (
        graph.caching_array(np.int32, -1),
        graph.caching_array(np.int32, -1),
        graph.caching_array(np.int32, -1)
    )

    def f_score(node):
        # return costs[node] + heuristics[node]
        # Favor closest to the end
        return costs[node] + heuristics[node], heuristics[node]

    heap = MinHeap(graph.caching_array(np.int32, -1), f_score)

    if isinstance(start, list):
        # multi-source
        for node in start:
            costs[node] = 0
            heuristics[node] = graph.heuristic(node, end)
            heap.push(node)
    else:
        # single-source
        costs[start] = 0
        heuristics[start] = graph.heuristic(start, end)
        heap.push(start)

    while heap:
        current_node = heap.extract_min()
        if current_node == end:
            break

        for nb, cost in graph.get_neighbors(current_node):
            # Have I met that guy ?
            if costs[nb] == -1:
                # Never met
                heuristics[nb] = graph.heuristic(nb, end)
                costs[nb] = costs[current_node] + cost
                predecessors[nb] = graph.hash(current_node)
                heap.push(nb)
            # Is it a better path ?
            elif costs[current_node] + cost < costs[nb]:
                # Definitely better
                costs[nb] = costs[current_node] + cost
                predecessors[nb] = graph.hash(current_node)
                # it has to be in the heap, otherwise, there is an error
                heap.update(nb)

    path, current = [end], end
    while predecessors[current] != -1:
        current = graph.de_hash(predecessors[current])
        path.insert(0, current)
    return path, costs

def shortest_path_no_heap_optimization(graph: Graph, start, end) -> tuple[list, np.ndarray]:
    """
    A* shortest path algorithm

    return path (and costs for visual debug purposes)
    """
    costs, heuristics, predecessors = (
        graph.caching_array(np.int32, -1),
        graph.caching_array(np.int32, -1),
        graph.caching_array(np.int32, -1)
    )

    def f_score(node):
        # return costs[node] + heuristics[node]
        # Favor closest to the end
        return costs[node] + heuristics[node], heuristics[node]

    heap = []

    if isinstance(start, list):
        # multi-source
        for node in start:
            costs[node] = 0
            heuristics[node] = graph.heuristic(node, end)
            heap.append(node)
    else:
        # single-source
        costs[start] = 0
        heuristics[start] = graph.heuristic(start, end)
        heap.append(start)

    while heap:
        index, current_node = min(enumerate(heap), key=lambda x: f_score(x[1]))
        heap.pop(index)
        if current_node == end:
            break

        for nb, cost in graph.get_neighbors(current_node):
            # Have I met that guy ?
            if costs[nb] == -1:
                # Never met
                heuristics[nb] = graph.heuristic(nb, end)
                costs[nb] = costs[current_node] + cost
                predecessors[nb] = graph.hash(current_node)
                heap.append(nb)
            # Is it a better path ?
            elif costs[current_node] + cost < costs[nb]:
                # Definitely better
                costs[nb] = costs[current_node] + cost
                predecessors[nb] = graph.hash(current_node)

    path, current = [end], end
    while predecessors[current] != -1:
        current = graph.de_hash(predecessors[current])
        path.insert(0, current)
    return path, costs


def shortest_path_c(grid: np.ndarray, start, end):
    """
    A* algorithm on grid graph, 8-connected, with heap optimization
    compiled in c
    """
    width, height = grid.shape
    start = width * start[1] + start[0]
    end = width * end[1] + end[0]
    result = c_astar(width, height, grid.ctypes.data_as(POINTER(c_uint8)), start, end)
    index, path = 0, []
    while result[index] != MAX_UINT32:
        x, y = divmod(result[index], height)
        path.append((x, y))
        index += 1
    return path


def simplify_path(path):
    i = 1
    while i < len(path) - 1:
        delta0: tuple[int, int] = (path[i][0] - path[i - 1][0]), (path[i][1] - path[i - 1][1])
        inv_norm0 = 1.0 / np.sqrt(delta0[0] ** 2 + delta0[1] ** 2)
        delta0[0] *= inv_norm0
        delta0[1] *= inv_norm0
        delta1: tuple[int, int] = (path[i + 1][0] - path[i][0]), (path[i + 1][1] - path[i][1])
        inv_norm1 = 1.0 / np.sqrt(delta1[0] ** 2 + delta1[1] ** 2)
        delta1[0] *= inv_norm1
        delta1[1] *= inv_norm1

        diff = delta0[0] - delta1[0], delta0[1] - delta1[1]

        if diff[0] ** 2 + diff[1] ** 2 < 0.1:
            del path[i]
        else:
            i += 1


def collide_on_line(pos_from: tuple[int, int], pos_to: tuple[int, int]) -> bool:
    x0 = min(pos_from[0], pos_to[0])
    x1 = max(pos_from[0], pos_to[0])
    y0 = min(pos_from[1], pos_to[1])
    y1 = max(pos_from[1], pos_to[1])

    dx = x1 - x0
    dy = y1 - y0
    if dx > dy:
        for x in range(int(x0), int(x1 + 1)):
            y = int(y0 + dy * (x - x1) / dx)
            if self.board[y][x] == 1:
                return True
        for y in range(int(y0), int(y1 + 1)):
            x = int(x0 + dx * (y - y1) / dy)
            if self.board[y][x] == 1:
                return True
    return False


def vectorize_path(path, pos: tuple[int, int]):
    for i in range(len(path) - 1, 0, -1):
        if not collide_on_line(pos, path[i]):
            for j in range(i - 1):
                path.pop(1)
            return


def shortest_vectorized_path(grid: np.ndarray, start, end):
    path = shortest_path_c(grid, start, end)

    simplify_path(path)
    vectorize_path(path, path[0])

    return path
