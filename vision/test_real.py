import time
import os
import cv2
import numpy as np
from .geometry import find_camera_position, render_multi_cam_cached_matrices, opencv_save_my_ass
from .aruco import BOARD_TAGS, detect, get_point_indices, filter_table_tags
from .camera import HDProWebcamC920, LogitechWebcamC930e
from .combinations import COMBINATIONS


import warnings
# TODO: comment this part to debug
# SHUT UP NUMPY, let me divide by 0, just put those 'NaN' quietly; opencv may shut up too... good luck
warnings.filterwarnings('ignore')

win_name = 'computer vision'
cv2.namedWindow(win_name)
width, height = 1920, 1080
img = np.zeros((height, width, 3), np.uint8)
img_buffer = img.copy()
PATH = os.path.dirname(__file__)

videos = left_vid, right_vid = cv2.VideoCapture(os.path.join(PATH, 'left.avi')), cv2.VideoCapture(os.path.join(PATH, 'right.avi'))
cameras = left_cam, right_cam = HDProWebcamC920(None, 1., width, height), LogitechWebcamC930e(None, 1., width, height)
VIDEO_INDEX, COMBINATION_INDEX, TEST_LINE = range(3)
context = [1, 0, [None, None]]
combination = []

MY_BASE_TO_CV2_BASE = np.array((
    (1., 0., 0.),
    (0., 0., -1.),
    (0., 1., 0.)
))
CV2_BASE_TO_MY_BASE = MY_BASE_TO_CV2_BASE.T


def shift_position(cnt):
    vid = videos[context[VIDEO_INDEX]]
    old = vid.get(cv2.CAP_PROP_POS_FRAMES)
    frame_count = vid.get(cv2.CAP_PROP_FRAME_COUNT)
    vid.set(cv2.CAP_PROP_POS_FRAMES, max(0, min(old + cnt-1, frame_count-1)))
    vid.read(img_buffer)

    ids, rects = detect(img_buffer)
    table_markers = filter_table_tags(ids)
    # table_markers = {x: ids[x] for x in ids if 0 <= x - 20 < 4}

    table_situation = sum(1 << (x - 20) for x, _ in table_markers)
    combination[:] = COMBINATIONS[table_situation]
    if len(combination):
        camera = cameras[context[VIDEO_INDEX]]
        obj_points = np.concatenate(tuple(BOARD_TAGS[x - 20] for x, _ in table_markers), axis=0)
        img_points = np.concatenate(tuple(rects[x] for _, x in table_markers), axis=0)
        camera.screw[:] = opencv_save_my_ass(obj_points, img_points, camera.get_opencv_camera_matrix())
        camera.make_transformation_matrix()
        rendered = render_multi_cam_cached_matrices(camera.transformation_matrix[None, ...], camera.projection_matrix[None, ...], BOARD_TAGS)
        cv2.polylines(img_buffer, np.int32(rendered[0]), True, (0, 255, 0), 4)

        points = get_point_indices(combination[context[COMBINATION_INDEX] % len(combination)])
        x, y = zip(*points)
        tags = BOARD_TAGS[list(x), list(y)]
        x, y = list(map(lambda _x: dict(table_markers)[_x+20], x)), list(y)
        circles = np.int32(rects[x, y])

        # chosen point to solve camera position
        for index, circle in enumerate(circles):
            cv2.circle(img_buffer, circle, 6, (255, 0, 255 * (index >= 2)), thickness=-1)

        pos0, ang0, pos1, ang1 = find_camera_position(tags, circles, camera.ray_matrix, camera.projection_matrix)
        camera.screw[:, 0] = pos0
        camera.screw[:, 1] = ang0
        camera.make_transformation_matrix()
        rendered = render_multi_cam_cached_matrices(camera.transformation_matrix[None, ...], camera.projection_matrix[None, ...], BOARD_TAGS)
        cv2.polylines(img_buffer, np.int32(rendered[0]), True, (0, 255, 255), 4)

        camera.screw[:, 0] = pos1
        camera.screw[:, 1] = ang1
        camera.make_transformation_matrix()
        rendered = render_multi_cam_cached_matrices(camera.transformation_matrix[None, ...], camera.projection_matrix[None, ...], BOARD_TAGS)
        # cv2.polylines(img_buffer, np.int32(rendered[0]), True, (255, 0, 255), 4)

        camera.screw[:, 0] = (pos1 + pos0) * .5
        camera.screw[:, 1] = (ang1 + ang0) * .5
        camera.make_transformation_matrix()
        rendered = render_multi_cam_cached_matrices(camera.transformation_matrix[None, ...], camera.projection_matrix[None, ...], BOARD_TAGS)
        # cv2.polylines(img_buffer, np.int32(rendered[0]), True, (0, 0, 0), 4)

        cv2.line(img_buffer, np.int32(circles[0]), np.int32(circles[1]), (255, 0, 0), 3)
        cv2.line(img_buffer, np.int32(circles[2]), np.int32(circles[3]), (0, 0, 255), 3)


    # cv2.polylines(img_buffer, np.int32(rects), True, (0, 0, 255), 2)
    img[:] = img_buffer


def change_cam():
    context[VIDEO_INDEX] ^= 1
    shift_position(0)


def change_comb(cnt):
    context[COMBINATION_INDEX] += cnt
    shift_position(0)


callbacks = {
    ord('n'): (shift_position, (1,)),
    ord('N'): (shift_position, (10,)),
    ord('p'): (shift_position, (-1,)),
    ord('P'): (shift_position, (-10,)),
    ord('c'): (change_cam, ()),
    ord('d'): (change_comb, (1,)),
    ord('s'): (change_comb, (-1,))
}

nothing = lambda: None


def handle_events(frame_rate=30.):
    date = time.perf_counter()
    keep_running = True
    while keep_running and time.perf_counter() - date < 1 / frame_rate:
        keep_running &= ((key := cv2.pollKey()) != ord('q'))
        keep_running &= (cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) > 0)
        fn, args = callbacks.get(key, (nothing, ()))
        fn(*args)
    return keep_running


def display():
    string = (
        f'\r{left_vid.get(cv2.CAP_PROP_POS_FRAMES)} / '
        f'{right_vid.get(cv2.CAP_PROP_POS_FRAMES)} / '
        f'{context[VIDEO_INDEX]} / '
        f'{context[COMBINATION_INDEX]}({len(combination)})'
    )
    print(string, end='')
    cv2.imshow(win_name, cv2.resize(img, (1280, 720)))


def mouse_callback(event, x, y, flags, param):
    if event != cv2.EVENT_LBUTTONDOWN:
        return
    line = context[TEST_LINE]
    if line[0] is None:
        line[0] = 1920 * x // 1280, 1920 * y // 1280
    elif line[1] is None:
        line[1] = 1920 * x // 1280, 1920 * y // 1280
        cv2.line(img, line[0], line[1], (0, 0, 0), 3)
    else:
        line[:] = None, None
        img[:] = img_buffer

cv2.setMouseCallback(win_name, mouse_callback)

shift_position(581)
running = True
while running:
    display()
    running = handle_events()
