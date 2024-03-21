from typing import Optional
import numpy
from min_heap_binary_tree import MinHeapBinaryTree, Comparison


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

    def update_grid(self, x: int, y: int, value: int):
        """
        Updates the value of the grid at a particular position.
        If said position is out of bounds, does nothing.
        """
        index = self.pos_to_index(x, y)
        if index is not None:
            self.grid[index] = value

    def pos_to_index(self, x: int, y: int) -> Optional[int]:
        """
        Get the index in the grid based off of the tuple x, y
        (returns None if the resulting index is out of bounds).
        """
        value = x + self.x_dim * y
        if not (0 <= value < len(self.grid)):
            return None
        return x + self.x_dim * y

    def index_to_pos(self, index: int) -> Optional[tuple]:
        """
        Get the position integer tuple (x, y) based off of the index
        in the grid (returns None if out of bounds).
        """
        if not (0 <= index < len(self.grid)):
            return None
        return index % self.x_dim, index // self.x_dim

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
        dimension = len(self.grid)
        parent: numpy.array = numpy.full(dimension, -1, dtype=int)
        # G: distance between the start position and the current position.
        g: numpy.array = numpy.full(dimension, -1, dtype=int)
        g[start_index] = 0
        # H: idealistic distance between the current position and the end position.
        h: numpy.array = numpy.array([self.distance_between(i, end_index) for i in range(dimension)], dtype=int)

        # list of two values, the first is the index, the second the value at that index.
        # The comparison is done on the value, hence index 1.
        to_search = MinHeapBinaryTree(lambda lhs, rhs: Comparison.from_int(lhs[1], rhs[1]))
        to_search.push([start_index, self.grid[start_index]])

        # List of int tuples of already searched cells in the grid.
        already_searched: list[list[int]] = []

        while not to_search.is_empty():
            # Get the value with the smallest value.
            current: list[int] = to_search.pop()
            current_index = current[0]
            current_value = current[1]

            already_searched.append(current)

            # Handle end case (we know that the path exists, no
            # need to handle the case where we don't reach the
            # start_index)
            if current_index == end_index:
                current_path_cell = end_index
                path: list[int] = []
                while parent[current_path_cell] != start_index:
                    path.append(current_path_cell)
                    current_path_cell = parent[current_path_cell]

                path.reverse()
                return path

            # Check all neighbours.
            for neighbour_index in self.get_valid_plus_neighbours(current_index):
                if neighbour_index in already_searched:
                    continue
                cost_to_neighbour = g[current_index] + 10

                # neighbour_in_search: bool = neighbour_index in to_search
                neighbour_in_search: bool = False
                for element in to_search.values:
                    if element[0] == neighbour_index:
                        neighbour_in_search = True
                        break

                if not neighbour_in_search or cost_to_neighbour < g[neighbour_index]:
                    g[neighbour_index] = cost_to_neighbour
                    parent[neighbour_index] = current_index

                    if not neighbour_in_search:
                        h[neighbour_index] = self.distance_between(neighbour_index, end_index)
                        # Add the neighbour's index and value to the list to search.
                        to_search.push([neighbour_index, self.grid[neighbour_index]])

            for neighbour_index in self.get_valid_x_neighbours(current_index):
                if neighbour_index in already_searched:
                    continue
                cost_to_neighbour = g[current_index] + 14

                neighbour_in_search: bool = False
                for element in to_search.values:
                    if element[0] == neighbour_index:
                        neighbour_in_search = True
                        break

                if not neighbour_in_search or cost_to_neighbour < g[neighbour_index]:
                    g[neighbour_index] = cost_to_neighbour
                    parent[neighbour_index] = current_index

                    if not neighbour_in_search:
                        h[neighbour_index] = self.distance_between(neighbour_index, end_index)
                        # Add the neighbour's index and value to the list to search.
                        to_search.push([neighbour_index, self.grid[neighbour_index]])

        # There is no path.
        return None
