import threading
import time
from hokuyolx import HokuyoLX
import comm
from comm import Asserv
from pathfinding.working_a_star import *
from vision.camera import Camera
from vision.geometry import sc_intersection

RUNNING, FPS = range(2)

TABLE = np.array(((
    (-1500., 0., 0.),
    (-1500., 2000., 0.),
    (1500., 2000., 0.),
    (1500., 0., 0.)
),))

PATHFINDING_RESOLUTION_X = 300
PATHFINDING_RESOLUTION_Y = 200
PATHFINDING_MIN_DISTANCE_TO_POINT = 10
PATHFINDING_THREAD_SLEEP_DURATION = 0.1

LIDAR_MIN_POSITION_X = 0
LIDAR_MAX_POSITION_X = 3000
LIDAR_MIN_POSITION_Y = 0
LIDAR_MAX_POSITION_Y = 2000

LIDAR_MIN_DISTANCE = 15
LIDAR_THREAD_SLEEP_DURATION = 0.1

# lidar = HokuyoLX()

# ray = np.random.uniform(0.0, 10.0, (1000000, 2))
# angle = ray.T[0][100:-100]
# distances = ray.T[1][100:-100]
# distance_threshold = distances < LIDAR_MIN_DISTANCE
# angle = angle[distance_threshold]
# distances = distances[distance_threshold]
# x, y = np.cos(angle) * distances, np.sin(angle) * distances
# x = x[x >= 0.0]
# x = x[x < 100.0]
# y = y[y >= 0.0]
# y = y[y < 100.0]
#
# if x.any() or y.any():
#     print("Ye")
# else:
#     print("Yeet")x


def pathfinding_thread_function(strategy: list, robot: Asserv, astar):
    # astar = AStar(PATHFINDING_RESOLUTION_X, PATHFINDING_RESOLUTION_Y)

    try:
        current_objective = strategy.pop(0)
    except IndexError:
        return

    # Loop through each strategic objective.
    while True:
        robot_position = robot.get_pos_xy()

        path = shortest_vectorized_path(astar.grid, robot_position, current_objective)
        # path = astar.find_path(
        #     astar.pos_to_index(robot_position[0], robot_position[1]),
        #     astar.pos_to_index(current_objective[0], current_objective[1]))

        while len(path) != 0:

            target_position = path.pop(0)

            # Break out of the inner loop if we are close enough to the current strategy's
            # position.
            distance_squared = ((target_position[0] - robot_position[0]) ** 2 +
                                (target_position[1] - robot_position[1]) ** 2)

            # Note: here the path is considered to be vectorized.
            if astar.has_updated_collider_since_last_path_calculation:
                path = shortest_vectorized_path(astar.grid, robot_position, current_objective)

                # Restart the loop just in case. (who knows?)
                continue

            try:
                current_rho_theta = robot.get_pos()
                delta_position = (target_position[0] - robot_position[0], target_position[1] - robot_position[1])
                delta_position_norm = (delta_position[0] ** 2 + delta_position[1] ** 2) ** 0.5
                delta_position_normalized = (delta_position[0] / delta_position_norm,
                                             delta_position[1] / delta_position_norm)
                # Dot product of the theta vector in cartesian coordinates by the vector from
                # out current position to the target position should give the cosine of the
                # angle between both vectors.
                theta = np.arccos(delta_position_normalized[0] * np.cos(current_rho_theta[1]) +
                                  delta_position_normalized[1] * np.sin(current_rho_theta[1]))

                # Rho is just the distance between the current position and the target
                # position.
                rho = delta_position_norm
                robot.move(rho, theta)

                # Wait until we reach the current point.
                distance_squared = delta_position_norm ** 2
                while distance_squared > PATHFINDING_MIN_DISTANCE_TO_POINT ** 2:
                    time.sleep(PATHFINDING_THREAD_SLEEP_DURATION)
                    robot_position = robot.get_pos_xy()
                    distance_squared = ((target_position[0] - robot_position[0]) ** 2 +
                                        (target_position[1] - robot_position[1]) ** 2)

            except IndexError:
                # We don't need to do anything here
                pass

        try:
            current_objective = strategy.pop(0)
        except IndexError:
            # There are no more things to do, so we stop the robot.
            break


def lidar_thread_function(robot: Asserv):
    lidar = HokuyoLX()
    while True:
        timestamp, scan = lidar.get_filtered_dist(dmax=50000)

        angle = scan.T[0][100:-100]
        distances = scan.T[1][100:-100]
        distance_threshold = distances < LIDAR_MIN_DISTANCE
        angle = angle[distance_threshold]
        distances = distances[distance_threshold]
        x, y = np.cos(angle) * distances, np.sin(angle) * distances
        x = x[x >= 0.0]
        x = x[x < 100.0]
        y = y[y >= 0.0]
        y = y[y < 100.0]

        if x.any() or y.any():
            robot.notify_stop()

        time.sleep(LIDAR_THREAD_SLEEP_DURATION)


def cam_thread(index, camera: Camera, shared, fps):
    try:
        while shared[RUNNING]:
            date = time.perf_counter()
            camera.read()
            # print('\r', 1 / (time.perf_counter() - date), end='')
            shared[FPS][index] = 1 / (time.perf_counter() - date)
            while time.perf_counter() - date < 1/fps:
                time.sleep(0.01)
                # shared[RUNNING] &= cv2.pollKey() != ord('q') and cv2.getWindowProperty(camera.name, cv2.WND_PROP_VISIBLE) > 0
    except Exception as _:
        shared[RUNNING] = False

def camera_thread_function(camera_classes: list[type[Camera]], shared, fps, astar):
    cameras = tuple(cls.new() for cls in camera_classes)

    for index, camera in enumerate(cameras):
        threading.Thread(target=cam_thread, args=(index, camera, shared, fps)).start()

    time.sleep(1.)

    while shared[RUNNING] and all(camera.stream is not None for camera in cameras):
        time.sleep(0.1)
        date = time.perf_counter()

        astar.grid.fill(0)
        for camera in cameras:
            # camera.read()
            camera.reposition(detect_markers=True)
            # img = np.array(camera.image)

            ids, rects = camera.detected
            if ids:
                sc_rect_centers = sc_intersection(rects.swapaxes(0, 1)[[0, 2, 1, 3]])
                re_rect_centers = np.int32(camera.to_real_world(sc_rect_centers))

                for i in range(re_rect_centers.len()):
                    if (-1500 < re_rect_centers[i][0] < 1500 and
                            0 < re_rect_centers[i][1] < 2000 and
                            40 < re_rect_centers[i][2] < 50):
                        astar[(re_rect_centers[i][0] + 1500) / 100, re_rect_centers[i][1] / 100] = 1


shared_vars = [True, [0.] * len(Camera.__subclasses__())]

robot_asserv = comm.make_asserv()

passed_astar = BinaryGridGraph(np.zeros(shape=(PATHFINDING_RESOLUTION_X, PATHFINDING_RESOLUTION_Y)))

pathfinding_thread = threading.Thread(
    target=pathfinding_thread_function, args=([], robot_asserv, passed_astar,))

lidar_thread = threading.Thread(
    target=lidar_thread_function, args=(robot_asserv,))

camera_thread = threading.Thread(
    target=camera_thread_function, args=([], Camera.__subclasses__(), shared_vars, 20, passed_astar, )
)

pathfinding_thread.join()
lidar_thread.join()
camera_thread.join()
