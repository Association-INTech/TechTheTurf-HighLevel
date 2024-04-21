"""
Most probably deprecated
"""

import time

import cv2
import numpy as np
from geometry import render_multi_cam_cached_matrices, find_camera_position
from aruco import BOARD_TAGS, get_point_indices
from combinations import COMBINATIONS
from camera import HDProWebcamC920

import warnings
# SHUT UP NUMPY, let me divide by 0, just put those 'NaN' quietly
warnings.filterwarnings('ignore')


win_name = 'F@#k computer vision'
cv2.namedWindow(win_name)
width, height = 800, 450
img = np.zeros((height, width, 3), np.uint8)
cam = HDProWebcamC920(None, 1., width, height)


def do_nothing():
    pass


def identity(x):
    return x


def update_value(array, index, callback=do_nothing, mapping=identity):
    def trackbar_callback(x):
        array[index] = mapping(x)
        callback()
    return trackbar_callback


TRACKBAR_VALUES = 50


def range_mapping(_min, _max):
    def mapping(x):
        return _min + (_max - _min) * x / TRACKBAR_VALUES
    return mapping


def deg_to_rad(x):
    return np.pi * x / 180


camera_screw = np.zeros((3, 2), float)
var_names, var_indices, var_ranges = (
    'x y z alpha beta gamma'.split(),
    ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)),
    ((-100, 100), (-50, 50), (1000, 2000), (deg_to_rad(-90), deg_to_rad(90)), (deg_to_rad(-90), deg_to_rad(0)), (deg_to_rad(-10), deg_to_rad(10)))
)

X, Y, Z = np.identity(3)
transformation_matrix = np.identity(4)


Kl = 237 / 310
projection = width * np.array(((
   (Kl, 0., 0., .5),
   (0., 0., -Kl, 9/32)
),))


def display():
    print('\r', end='')
    for var_name, var_index in zip(var_names, var_indices):
        print(f'{var_name} : {cam.screw[var_index]:.03f} ;  ', end='')
    cam.make_transformation_matrix()
    rendered, = render_multi_cam_cached_matrices(cam.transformation_matrix[None, ...], cam.projection_matrix[None, ...], BOARD_TAGS)
    cv2.polylines(img, np.int32(rendered), True, (255, 255, 255))

    ids = {20: 0, 21: 1, 22: 2, 23: 3}
    combination = COMBINATIONS[15]
    points = get_point_indices(combination[0])
    x, y = zip(*points)
    tags = BOARD_TAGS[list(x), list(y)]
    x, y = list(map(lambda _x: ids[_x+20], x)), list(y)
    circles = np.int32(rendered[x, y])
    # chosen point to solve camera position
    for index, circle in enumerate(circles):
        cv2.circle(img, circle, 6, (255, 0, 255 * (index >= 2)), thickness=-1)

    camera = HDProWebcamC920(None, 1., width, height)

    pos0, ang0, pos1, ang1 = find_camera_position(circles, tags, cam.ray_matrix)
    print(pos0, ang0, pos1, ang1)
    camera.screw[:, 0] = pos0
    camera.screw[:, 1] = ang0
    camera.make_transformation_matrix()
    rendered = render_multi_cam_cached_matrices(camera.transformation_matrix[None, ...], camera.projection_matrix[None, ...], BOARD_TAGS)
    cv2.polylines(img, np.int32(rendered[0]), True, (0, 255, 255), 4)

    camera.screw[:, 0] = pos1
    camera.screw[:, 1] = ang1
    camera.make_transformation_matrix()
    rendered = render_multi_cam_cached_matrices(camera.transformation_matrix[None, ...],
                                                camera.projection_matrix[None, ...], BOARD_TAGS)
    cv2.polylines(img, np.int32(rendered[0]), True, (255, 0, 255), 4)

    cv2.imshow(win_name, img)
    img[:] = 0


for index, var_name, var_index, (var_min, var_max) in zip(range(6), var_names, var_indices, var_ranges):
    def_value = TRACKBAR_VALUES // 2 if index != 4 else 17
    callback = update_value(cam.screw, var_index, display, range_mapping(var_min, var_max))
    cv2.createTrackbar(var_name, win_name, def_value, TRACKBAR_VALUES, callback)
    callback(def_value)
display()

running = True
cv2.imshow(win_name, img)
while running and cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE):
    date = time.perf_counter()
    while running and time.perf_counter() - date < 0.03:
        running &= cv2.pollKey() not in (ord('q'), 27)

cv2.destroyAllWindows()
