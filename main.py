import numpy as np

from order import *

from map import *
from matplotlib import pyplot as plt
import threading

from Lidar import *

MIN_X = 10 # To change
MIN_Y = 10 # To change
MAX_X = 100 # To change
MAX_Y = 100 # To change
MIN_DISTANCE = 10 # To change


# while True:
#     order = get_order()
#     if order is None:
#         continue
#     order.print()


class RobotState:
    def __init__(self):
        self.position = Vec2(0, 0)
        self.orientation = 0.0
        self.target_position = Vec2(0, 99)


def draw_line_sequence(seq, col):
    if len(seq) <= 1:
        return
    for j in range(len(seq) - 1):
        plt.plot(
            [seq[j][0], seq[j + 1][0]],
            [seq[j][1], seq[j + 1][1]],
            color=col, linestyle="-")


def move(to):
    return to


def movement_thread_fn(graph, robot_state):
    while True:
        # Todo
        pass


def process_close_object():
    print("There is a object that is close.")


def main():
    robot_state = RobotState()
    graph = Map(100, 100)
    lidar = HokuyoLX()

    for i in range(0, 60):
        graph.update_collider(Vec2(50, i), 1)

    movement_thread = threading.Thread(target=movement_thread_fn, args=(graph, robot_state,))
    movement_thread.start()
    current_position = Vec2(0, 0)
    while True:
        # plt.imshow(graph.board)
        # plt.show()
        # Update the graph
        # graph.update_collider_with_lidar(
        #     robot_state.position,
        #     robot_state.orientation,
        #     lidar,
        #     1024
        # )
        # seq = [[a.x, a.y] for a in graph.lidar_collider_list]
        # seq = graph.tmp_angle_dist
        # print(seq)
        # plt.plot([a[0] for a in seq], [a[1] for a in seq], "b")
        # plt.show()
        # fig = plt.figure()
        # ax = fig.add_subplot(projection="polar")
        # ax.scatter([a[0] for a in seq], [a[1] for a in seq])
        # plt.show()
        # graph.get_path(robot_state.position, robot_state.target_position)
        # draw_line_sequence(graph.path, "b")
        # print(graph.path)
        # plt.imshow(graph.visited, interpolation='none')
        # plt.show()
        timestamp, scan = lidar.get_filtered_dist(dmax=50000)
        angles = [i / len(scan) * 2.0 * np.pi * (280 / 360) for i in range(len(scan))]
        distances = scan
        assert(len(angles) == len(distances)) # Not useful?
        for i in range(len(angles)):
            offset_position: Vec2 = Vec2(np.cos(angles[i]), np.sin(angles[i])).scale(distances[i])
            position = robot_state.position.add(offset_position)
            if not (MIN_X < position.x < MAX_X) or not (MIN_Y < position.y < MAX_Y):
                continue
            if offset_position.length() < MIN_DISTANCE:
                process_close_object()



    # movement_thread.join()


if __name__ == '__main__':
    # lidar = HokuyoLX()
    # timestamp, scan = lidar.get_filtered_dist(dmax=50000)
    # figure = plt.figure()
    # ax = figure.add_subplot(projection="polar")
    # x = [i / len(scan) * 2.0 * np.pi * (280 / 360) for i in range(len(scan))]
    # y = scan
    # np.cos(x) + robot_state
    # ax.plot(x, y)
    # plt.show()
    # ax = figure.add_subplot()
    # print("Timestamp")
    # print(timestamp)
    # print("Scan")
    # print(scan)

    main()
