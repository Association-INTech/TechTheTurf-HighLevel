from .camera import LogitechWebcamC930e, HDProWebcamC920
from .combinations import COMBINATIONS
from .aruco import BOARD_TAGS, get_point_indices
from .geometry import *
import time


win_name = 'computer vision'
width, height = 1600, 900
border_height = 60
img = np.zeros((height+border_height, width, 3), np.uint8)
IMG = img[:height]

TEXT_COLOR = 255, 255, 255
FONT = cv2.FONT_HERSHEY_SIMPLEX
SCALE = .8

camera_screw = np.array((
    (0., 0.),
    (-50., -np.pi * .25),
    (1600., 0.)
))
cam, cam_test = LogitechWebcamC930e(None, 1., width, height), LogitechWebcamC930e(None, 1., width, height)
cam.screw = camera_screw

nothing = (lambda: None),

COMB_INDEX, SITUATION_INDEX = range(2)
context = [0, 15]

def render():
    x, alpha, y, beta, z, gamma = camera_screw.flat
    string = f'x = {x:0.2f}; y = {y:0.2f}; z = {z:0.2f}; alpha = {alpha:0.4f}; beta = {beta:0.4f}; gamma = {gamma:0.4f}'
    img[-border_height:, :] = 64
    IMG[:] = 32

    # center text
    (w, h), _ = cv2.getTextSize(string, FONT, SCALE, 1)
    org = (width - w) // 2, height+(border_height+h) // 2
    # draw text
    cv2.putText(img, string, org, FONT, SCALE, TEXT_COLOR, 1, cv2.LINE_AA)

    cam.make_transformation_matrix()
    ideal_rendered_tags, = render_multi_cam_cached_matrices(
        cam.transformation_matrix[None],
        cam.projection_matrix[None],
        BOARD_TAGS
    )
    cv2.polylines(IMG, np.int32(ideal_rendered_tags), True, TEXT_COLOR, 1)

    obj_points = np.concatenate(tuple(BOARD_TAGS[x] for x in range(4)), axis=0)
    img_points = np.concatenate(tuple(ideal_rendered_tags[x] for x in range(4)), axis=0)
    cam_test.screw[:] = opencv_save_my_ass(obj_points, img_points, cam_test.get_opencv_camera_matrix())
    cam_test.make_transformation_matrix()
    test_rendered_tags, = render_multi_cam_cached_matrices(
        cam_test.transformation_matrix[None],
        cam_test.projection_matrix[None],
        BOARD_TAGS
    )
    cv2.polylines(IMG, np.int32(test_rendered_tags), True, (255, 0, 0), 4)

    # print(img_points, obj_points)
    # ret, ori, vec,  = cv2.solvePnP(obj_points, img_points, cam_test.get_opencv_camera_matrix(), None)
    # cv2.Rodrigues(ori)
    # print('\nRodrigues')
    # r = cv2.Rodrigues(-ori)[0]
    # print(r @ vec[:, 0], find_orientation(r))


    combination = COMBINATIONS[context[SITUATION_INDEX] % 16]
    if len(combination):
        points = get_point_indices(combination[context[COMB_INDEX] % len(combination)])
        x, y = zip(*points)
        sc_points = ideal_rendered_tags[list(x), list(y)]
        re_points = BOARD_TAGS[list(x), list(y)]

        cam0, ori0, cam1, ori1 = find_camera_position(re_points, sc_points, cam.ray_matrix, cam.projection_matrix)
        cam_test.screw[:, 0] = cam0
        cam_test.screw[:, 1] = ori0
        cam_test.make_transformation_matrix()
        test_rendered_tags, = render_multi_cam_cached_matrices(
            cam_test.transformation_matrix[None],
            cam_test.projection_matrix[None],
            BOARD_TAGS
        )
        cv2.polylines(IMG, np.int32(test_rendered_tags), True, (0, 0, 0), 2)

        re_inter = re_intersection(re_points)
        rendered_re_inter, = render_multi_cam_cached_matrices(
            cam.transformation_matrix[None],
            cam.projection_matrix[None],
            re_inter
        )
        cv2.circle(IMG, np.int32(rendered_re_inter), 10, TEXT_COLOR, -1)

        sc_inter = sc_intersection(sc_points)
        cv2.circle(IMG, np.int32(sc_inter), 6, (192, 0, 128), -1)

        cv2.line(IMG, np.int32(sc_points[0]), np.int32(sc_points[1]), (255, 0, 0), 1)
        cv2.line(IMG, np.int32(sc_points[2]), np.int32(sc_points[3]), (0, 0, 255), 1)

    cv2.imshow(win_name, img)


def change_position(index, increment):
    camera_screw[index] += increment
    render()


def shift_combination(increment):
    context[COMB_INDEX] += increment
    render()


def shift_situation(increment):
    context[SITUATION_INDEX] += increment
    render()


events = {
    ord('a'): (change_position, (0, 0), +10),
    ord('A'): (change_position, (0, 0), -10),
    ord('z'): (change_position, (1, 0), +10),
    ord('Z'): (change_position, (1, 0), -10),
    ord('e'): (change_position, (2, 0), +10),
    ord('E'): (change_position, (2, 0), -10),
    ord('r'): (change_position, (0, 1), +np.pi / 100),
    ord('R'): (change_position, (0, 1), -np.pi / 100),
    ord('t'): (change_position, (1, 1), +np.pi / 100),
    ord('T'): (change_position, (1, 1), -np.pi / 100),
    ord('y'): (change_position, (2, 1), +np.pi / 100),
    ord('Y'): (change_position, (2, 1), -np.pi / 100),
    ord('d'): (shift_combination, +1),
    ord('s'): (shift_combination, -1),
    ord('x'): (shift_situation, +1),
    ord('c'): (shift_situation, -1),
}


def handle_events(frame_rate=60.):
    date = time.perf_counter()
    keep_running = True
    while keep_running and time.perf_counter() - date < 1 / frame_rate:
        key = cv2.pollKey()
        keep_running &= key != ord('q') and cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) > 0
        func, *args = events.get(key, nothing)
        func(*args)
    return keep_running


render()
cv2.imshow(win_name, img)

running = True
while running:
    running = handle_events()
