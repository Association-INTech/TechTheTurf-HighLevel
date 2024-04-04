# import threading
# import time
from hokuyolx import HokuyoLX
import numpy as np
# import comm
# from comm import Asserv
# from pathfinding.a_star import AStar
# use std::time::Instant;
#
# const MIN_DISTANCE: f32 = 0.5;
#
# fn main() {
#     let ray: Vec<(f32, f32)> = (0..1_000_000).map(|_| (0.0, 0.0)).collect();
#     let start = Instant::now();
#
#     let should_stop = ray
#         .iter()
#         .filter(|elem| elem.1 < MIN_DISTANCE)
#         .map(|polar| (polar.0.cos() * polar.1, -polar.0.sin() * polar.1))
#         .filter(|cart| cart.0 >= 0.0 && cart.0 < 100.0 && cart.1 >= 0.0 && cart.1 < 100.0)
#         .count()
#         != 0;
#
#     println!("{should_stop}: {:?}", start.elapsed());
# }


PATHFINDING_RESOLUTION_X = 100
PATHFINDING_RESOLUTION_Y = 100
PATHFINDING_MIN_DISTANCE_TO_POINT = 1
PATHFINDING_THREAD_SLEEP_DURATION = 0.1

LIDAR_MIN_POSITION_X = 0
LIDAR_MAX_POSITION_X = 100
LIDAR_MIN_POSITION_Y = 0
LIDAR_MAX_POSITION_Y = 100

LIDAR_MIN_DISTANCE = 3
LIDAR_THREAD_SLEEP_DURATION = 0.1

# lidar = HokuyoLX()

ray = np.random.uniform(0.0, 10.0, (1000000, 2))
angle = ray.T[0][100:-100]
distances = ray.T[1][100:-100]
distance_threshold = distances < LIDAR_MIN_DISTANCE
angle = angle[distance_threshold]
distances = distances[distance_threshold]
x, y = np.cos(angle) * distances, np.sin(angle) * distances
x = x[x >= 0.0]
x = x[x < 100.0]
y = y[y >= 0.0]
y = y[y < 100.0]

if x.any() or y.any():
    print("Ye")
else:
    print("Yeet")

#
# def pathfinding_thread_function(strategy: list, robot: Asserv):
#     astar = AStar(PATHFINDING_RESOLUTION_X, PATHFINDING_RESOLUTION_Y)
#
#     try:
#         current_objective = strategy.pop(0)
#     except IndexError:
#         return
#
#     # Loop through each strategic objective.
#     while True:
#         robot_position = robot.get_pos_xy()
#
#         path = astar.find_path(
#             astar.pos_to_index(robot_position[0], robot_position[1]),
#             astar.pos_to_index(current_objective[0], current_objective[1]))
#
#         while len(path) != 0:
#             target_position = astar.index_to_pos(path.pop(0))
#
#             # Break out of the inner loop if we are close enough to the current strategy's
#             # position.
#             distance_squared = ((target_position[0] - robot_position[0]) ** 2 +
#                                 (target_position[1] - robot_position[1]) ** 2)
#
#             # Note: here the path is considered to be vectorized.
#             if astar.has_updated_since_last_path:
#                 path = astar.find_path(
#                     astar.pos_to_index(robot_position[0], robot_position[1]),
#                     astar.pos_to_index(current_objective[0], current_objective[1]))
#
#                 # Restart the loop just in case. (who knows?)
#                 continue
#             try:
#                 current_rho_theta = robot.get_pos()
#                 delta_position = (target_position[0] - robot_position[0], target_position[1] - robot_position[1])
#                 delta_position_norm = (delta_position[0] ** 2 + delta_position[1] ** 2) ** 0.5
#                 delta_position_normalized = (delta_position[0] / delta_position_norm,
#                                              delta_position[1] / delta_position_norm)
#                 # Dot product of the theta vector in cartesian coordinates by the vector from
#                 # out current position to the target position should give the cosine of the
#                 # angle between both vectors.
#                 theta = np.arccos(delta_position_normalized[0] * np.cos(current_rho_theta[1]) +
#                                   delta_position_normalized[1] * np.sin(current_rho_theta[1]))
#
#                 # Rho is just the distance between the current position and the target
#                 # position.
#                 rho = delta_position_norm
#                 robot.move(rho, theta)
#
#                 # Wait until we reach the current point.
#                 distance_squared = delta_position_norm ** 2
#                 while distance_squared > PATHFINDING_MIN_DISTANCE_TO_POINT ** 2:
#                     time.sleep(PATHFINDING_THREAD_SLEEP_DURATION)
#                     robot_position = robot.get_pos_xy()
#                     distance_squared = ((target_position[0] - robot_position[0]) ** 2 +
#                                         (target_position[1] - robot_position[1]) ** 2)
#
#             except IndexError:
#                 # We don't need to do anything here
#                 pass
#
#         try:
#             current_objective = strategy.pop(0)
#         except IndexError:
#             # There are no more things to do, so we stop the robot.
#             break
#
#
# def lidar_thread_function(robot: Asserv):
#     lidar = HokuyoLX()
#     while True:
#         timestamp, scan = lidar.get_filtered_dist(dmax=50000)
#         angles = [i / len(scan) * 2.0 * np.pi * (280 / 360) for i in range(len(scan))]
#         distances: np.ndarray = np.array(scan)
#
#         is_near_object = False
#
#         for i in range(len(angles)):
#             robot_position = robot.get_pos_xy()
#             offset_position = (np.cos(angles[i]) * distances[i], np.sin(angles[i]) * distances[i])
#             position = (robot_position[0] + offset_position[0], robot_position[0] + offset_position[1])
#             # offset_position: Vec2 = Vec2(np.cos(angles[i]), np.sin(angles[i])).scale(distances[i])
#             # position = robot_state.position.add(offset_position)
#             if (not (LIDAR_MIN_POSITION_X < position[0] < LIDAR_MAX_POSITION_X) or
#                     not (LIDAR_MIN_POSITION_X < position[1] < LIDAR_MAX_POSITION_Y)):
#                 continue
#
#             distance_squared = offset_position[0] ** 2 + offset_position[1] ** 2
#             if distance_squared < LIDAR_MIN_DISTANCE ** 2:
#                 is_near_object = True
#                 # We currently only care if there is an object nearby.
#                 break
#
#         if is_near_object:
#             robot.notify_stop()
#
#         time.sleep(LIDAR_THREAD_SLEEP_DURATION)


# robot_asserv = comm.make_asserv()
#
# pathfinding_thread = threading.Thread(target=pathfinding_thread_function, args=([], robot_asserv,))
# lidar_thread = threading.Thread(target=lidar_thread_function, args=(robot_asserv,))
#
# pathfinding_thread.join()
# lidar_thread.join()

