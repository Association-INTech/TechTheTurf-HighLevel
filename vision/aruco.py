import cv2
import numpy as np
from .geometry import Z, mixt
import os

PATH = os.path.dirname(__file__)

BOARD_TAGS = np.array((
    ((800., 450., 0.),   (700., 450., 0.),   (700., 550., 0.),   (800., 550., 0.)),    # Tag 20
    ((-700., 450., 0.),  (-800., 450., 0.),  (-800., 550., 0.),  (-700., 550., 0.)),   # Tag 21
    ((800., 1450., 0.),  (700., 1450., 0.),  (700., 1550., 0.),  (800., 1550., 0.)),   # Tag 22
    ((-700., 1450., 0.), (-800., 1450., 0.), (-800., 1550., 0.), (-700., 1550., 0.)),  # Tag 23
    # ((50, -50, 0.), (-50, -50, 0.), (-50, 50, 0.), (50, 50, 0.))
))

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)


def detect(frame):
    """
    Detects aruco markers on an image

    :param frame: image to analyse
    :return: tuple[Tag_ids], np.ndarray[rectangle_index, 4, xy]
    """
    corners, ids, _ = detector.detectMarkers(frame)
    return ((), np.array(())) if ids is None else (
        tuple((i, index) for index, (i,) in enumerate(ids)),
        np.array(corners)[:, 0, :, :]
    )


def filter_table_tags(marker_ids: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return tuple(filter(lambda x: 0 <= x[0] - 20 < 4, marker_ids))


def group_by_marker_id(markers: tuple[tuple[int, int], ...]) -> dict[int, list[int]]:
    result = {}
    for marker_id, index in markers:
        if marker_id not in result:
            result[marker_id] = [index]
        else:
            result[marker_id].append(index)
    return result


"""
The functions below are deprecated
"""


def get_point_index(pair_index, shift=0):
    return (pair_index >> (4 * shift + 2)) & 0b11, (pair_index >> (4 * shift)) & 0b11


def make_all_combinations():
    valid_diagonals = {
        i: [] for i in range(16)
    }
    for point_pair_index in range(16 ** 4):
        points = pt1, pt2, pt3, pt4 = tuple(get_point_index(point_pair_index, i) for i in range(4))
        # I want 4 different points
        if len(set(points)) != 4:
            continue
        # only 1 arrangement
        if not (pt1 < pt2 and pt1 < pt3 < pt4):
            continue
        # No collinear diagonals
        v1, v2 = BOARD_TAGS[pt2] - BOARD_TAGS[pt1], BOARD_TAGS[pt4] - BOARD_TAGS[pt3]
        if abs(dd := mixt(Z, v1, v2)) < 1e-9:
            continue
        # diagonal intersection can't be one point
        inter = BOARD_TAGS[pt3] + v2 * mixt(Z, v1, BOARD_TAGS[pt1] - BOARD_TAGS[pt3]) / dd
        x, y = zip(*points)
        if (np.sum((BOARD_TAGS[list(x), list(y)] - inter[None, :]) ** 2, axis=1) ** .5).min() < 1e-1:
            continue
        mask = 0
        for tag, _ in points:
            mask |= 1 << tag
        valid_diagonals[mask].append(point_pair_index)
        # cnt, rest = sum((mask >> j) & 1 for j in range(4)), tuple(filter(lambda _x: ((mask >> _x) & 1) ^ 1, range(4)))
        # for sub_subset_index in range(1, 1 << (4 - cnt)):
        #     subset_index = mask + sum(((sub_subset_index >> i) & 1) << r for i, r in enumerate(rest))
        #     valid_diagonals[subset_index].append(point_pair_index)

    return valid_diagonals


all_combinations_template = """\"\"\"
All possible diagonal choices to process camera position given a set of markers from the table
Used in `find_camera_position`
\"\"\"


# Combination index: one hot encoding determining which marker is visible:
# 23 | 22 | 21 | 20

# Combination value: 4x 4-bit value identifying a marker corner:
# marker3 | corner3 | marker2 | corner2 | marker1 | corner1 | marker0 | corner0

# diagonals are formed with pairs 0-1 and 2-3

# Corner indexation:
#   2 ---- 3
#   |      |
#   |      |
#   1 ---- 0
# e.g.: 12576_10 = 11000100100000_2
# marker 20 corner 0
# marker 20 corner 2
# marker 20 corner 1
# marker 20 corner 3

COMBINATIONS = {{
    {}
}}
"""


combination_path = os.path.join(PATH, 'combinations.py')
if not os.path.exists(combination_path):
    with open(combination_path, 'w') as file:
        file.write(all_combinations_template.format(
            ',\n    '.join(f'{key}: {value}' for key, value in make_all_combinations().items())
        ))


def get_point_indices(point_pair_index):
    return tuple(get_point_index(point_pair_index, i) for i in range(4))
