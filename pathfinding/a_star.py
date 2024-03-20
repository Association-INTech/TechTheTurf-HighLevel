import numpy


class AStar:
    """
    A* Algorithm implementation on a static grid of values.

    Attributes:
    -----------
    grid: numpy.ndarray
        The 2D array of cells that comprise our map.
    """

    grid: numpy.ndarray

    def __init__(self, x_dim: int, y_dim: int):
        """
        Parameters:
        -----------
        x_dim: int
            The amount of cells along the X axis.
        y_dim: int
            The amount of cells along the Y axis.
        """
        self.grid = numpy.zeros(shape=(x_dim, y_dim))

    def update_collider(self, pos: (int, int), value: int):
        pass
