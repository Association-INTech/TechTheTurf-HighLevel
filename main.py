from order import *

from map import *
from matplotlib import pyplot as plt

from Lidar import *

# while True:
#     order = get_order()
#     if order is None:
#         continue
#     order.print()


def draw_line_sequence(seq, col):
    if len(seq) <= 1:
        return
    for j in range(len(seq) - 1):
        plt.plot(
            [seq[j][0], seq[j + 1][0]],
            [seq[j][1], seq[j + 1][1]],
            color=col, linestyle="-")


if __name__ == '__main__':
    graph = Map(100, 100)
    for i in range(0, 60):
        graph.update_collider((50, i), 1)

    graph.get_path((0, 0), (99, 0))
    draw_line_sequence(graph.path, "b")
    print(graph.path)
    plt.imshow(graph.visited, interpolation='none')
    plt.show()
