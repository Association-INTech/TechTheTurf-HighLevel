from typing import Optional
import numpy
import numpy as np

from min_heap_binary_tree import MinHeapBinaryTree
import sys

class AStar:
    """
    A* Algorithm implementation on a static grid of values.

    Attributes:
    -----------
    grid: numpy.ndarray
        The 2D array of cells that comprise our map.
    """

    # 1D array of numbers corresponding to all the points
    # in the grid of cells that is the map.
    grid: numpy.array

    # Amount of cells along the X axis.
    x_dim: int
    # Amount of cells along the Y axis.
    y_dim: int

    has_updated_since_last_path: bool

    def __init__(self, x_dim: int, y_dim: int):
        """
        Parameters:
        -----------
        x_dim: int
            The amount of cells along the X axis.
        y_dim: int
            The amount of cells along the Y axis.
        """
        self.grid = numpy.zeros(shape=x_dim*y_dim)
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.has_updated_since_last_path = False

    def update_grid(self, x: int, y: int, value: int):
        """
        Updates the value of the grid at a particular position.
        If said position is out of bounds, does nothing.
        """
        index = self.pos_to_index(x, y)
        if index is not None:
            self.grid[index] = value
            self.has_updated_since_last_path = True

    def pos_to_index(self, x: int, y: int) -> Optional[int]:
        """
        Get the index in the grid based off of the tuple x, y
        (returns None if the resulting index is out of bounds).
        """
        if x < 0 or y < 0:
            return None
        length: int = len(self.grid)
        value: int = x + self.x_dim * y
        if not (0 <= value < length):
            return None
        return x + self.x_dim * y

    def index_to_pos(self, index: int) -> Optional[tuple]:
        """
        Get the position integer tuple (x, y) based off of the index
        in the grid (returns None if out of bounds).
        """
        length: int = len(self.grid)

        if not (0 <= index < length):
            return None
        return index % self.x_dim, index // self.x_dim

    def get_valid_neighbours(self, index) -> Optional[list[tuple]]:
        if not (0 <= index < len(self.grid)):
            return None

        result = []
        x, y = self.index_to_pos(index)

        neighbour = self.pos_to_index(x - 1, y)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append((neighbour, 10))

        neighbour = self.pos_to_index(x + 1, y)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append((neighbour, 10))

        neighbour = self.pos_to_index(x, y - 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append((neighbour, 10))

        neighbour = self.pos_to_index(x, y + 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append((neighbour, 10))

        neighbour = self.pos_to_index(x - 1, y - 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append((neighbour, 14))

        neighbour = self.pos_to_index(x + 1, y - 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append((neighbour, 14))

        neighbour = self.pos_to_index(x - 1, y + 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append((neighbour, 14))

        neighbour = self.pos_to_index(x + 1, y + 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append((neighbour, 14))

        return result

    def get_valid_plus_neighbours(self, index: int) -> list[int]:
        """
        Get the list of indices of valid "+" neighbours (that is, that we can
        traverse by moving left, right, up or down and that are not blocked or out
        of bounds).
        """
        result = []
        x, y = self.index_to_pos(index)

        neighbour = self.pos_to_index(x - 1, y)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append(neighbour)

        neighbour = self.pos_to_index(x + 1, y)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append(neighbour)

        neighbour = self.pos_to_index(x, y - 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append(neighbour)

        neighbour = self.pos_to_index(x, y + 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append(neighbour)

        return result

    def get_valid_x_neighbours(self, index: int) -> list[int]:
        """
        Get the list of indices of valid "x" neighbours (that is, that we can
        traverse by moving up left, up right, bottom left or bottom right and
        that are not blocked or out of bounds).
        """
        result = []
        x, y = self.index_to_pos(index)

        neighbour = self.pos_to_index(x - 1, y - 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append(neighbour)

        neighbour = self.pos_to_index(x + 1, y - 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append(neighbour)

        neighbour = self.pos_to_index(x - 1, y + 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append(neighbour)

        neighbour = self.pos_to_index(x + 1, y + 1)
        if neighbour is not None and self.grid[neighbour] == 0:
            result.append(neighbour)

        return result

    def distance_between(self, start_index: int, end_index: int) -> int:
        """
        Gives the minimum distance between the start index's position
        and the end index's position (may not be the actual distance
        between both positions, as it may be overly optimistic).
        The end value is scaled by 10.
        """
        # Explanation:
        #               /| ^
        #             /  | | min
        # ----------/----| v
        # <------------->
        #       max
        # <--------><---->
        # max - min   min
        # Traverse max - min, than min * sqrt(2)
        # we multiply all by 10 and make it integers,
        # so we have 10(max - min) + 14 * min
        # which gives 10 max + 4 min
        start_x, start_y = self.index_to_pos(start_index)
        end_x, end_y = self.index_to_pos(end_index)

        dx = abs(end_x - start_x)
        dy = abs(end_y - start_y)

        minimum, maximum = min(dx, dy), max(dx, dy)

        return 10 * maximum + 4 * minimum

    def find_path(self, start_index: int, end_index: int) -> Optional[list[int]]:
        self.has_updated_since_last_path = True

        dimension = len(self.grid)
        parent: numpy.array = numpy.full(dimension, -1, dtype=int)
        # G: distance between the start position and the current position.
        g: numpy.array = numpy.full(dimension, sys.maxsize, dtype=int)
        g[start_index] = 0
        # H: idealistic distance between the current position and the end position.
        h: numpy.array = numpy.array([self.distance_between(i, end_index) for i in range(dimension)], dtype=int)

        # list of two values, the first is the index, the second the value at that index.
        # The comparison is done on the value, hence index 1.
        to_search = MinHeapBinaryTree(lambda i: g[i] + h[i], np.array([-1 for _ in range(dimension)]))
        to_search.push(start_index)

        # List of int tuples of already searched cells in the grid.
        # already_searched: list[int] = []

        while not to_search.is_empty():
            # to_search.display()
            # Get the value with the smallest value.
            current_index: int = to_search.pop()

            # already_searched.append(current_index)

            # Handle end case (we know that the path exists, no
            # need to handle the case where we don't reach the
            # start_index)
            if current_index == end_index:
                current_path_cell = end_index
                path: list[int] = []
                while current_path_cell != start_index:
                    path.append(current_path_cell)
                    current_path_cell = parent[current_path_cell]
                path.reverse()
                return path

            # Check all neighbours.
            for neighbour_index, distance in self.get_valid_neighbours(current_index):
                # if neighbour_index in already_searched:
                #     continue
                cost_to_neighbour = g[current_index] + distance

                if cost_to_neighbour < g[neighbour_index]:
                    g[neighbour_index] = cost_to_neighbour
                    parent[neighbour_index] = current_index

                    # neighbour_in_search = False
                    # for element in to_search.values:
                    #     if element == neighbour_index:
                    #         neighbour_in_search = True
                    #         element[1] = min(element[1], g[neighbour_index] + h[neighbour_index])
                    #         break

                    if to_search.location[neighbour_index] == -1:
                        to_search.push(neighbour_index)
                    else:
                        to_search.update(to_search.location[neighbour_index])
                        to_search.display()
                        assert to_search.guarantee_integrity()

        # There is no path.
        return None

    # def vectorize_path(self, path) -> list[int]:
    #     for i in range(len(path) - 1, 0, -1):
    #         if not self.collides_on_line(pos, path[i]):
    #             for j in range(i - 1):
    #                 path.pop(1)
    #             return

    def collides_on_line(self, from_x, from_y, to_x, to_y):
        x0 = min(from_x, to_x)
        x1 = max(from_x, to_x)
        y0 = min(from_y, to_y)
        y1 = max(from_y, to_y)

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