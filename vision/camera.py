import os

import numpy as np
from .geometry import axle_rotation, X, Y, Z, opencv_save_my_ass, screen_to_ray, dot, mat_x, re_intersection, sign
from .aruco import detect, BOARD_TAGS, filter_table_tags, rects_from_ids, ROBOT_MARKER_HEIGHT
import cv2
import platform

MJPG_CODEC = cv2.VideoWriter_fourcc(*'MJPG')
print('MJPG: ', MJPG_CODEC)
# MJPG_CODEC = 1196444237  # Hardcoded value so that pycharm shuts the f@#k up
# Pycharm can't find any documentation about VideoWriter_fourcc

if platform.system() == 'Windows':
    from pygrabber.dshow_graph import FilterGraph
    __g = FilterGraph()

    def get_available_cameras():
        devices = __g.get_input_devices()
        return dict(map(lambda x: x[::-1], enumerate(devices)))

else:
    def get_available_cameras():
        results = map(lambda cam_cls: (cam_cls.name, os.popen(f'readlink -f {cam_cls.linux_v4l_location}').read().split('\n')[0]), (LogitechWebcamC930e, HDProWebcamC920))
        return dict(filter(lambda pair: pair[1], results))


I, J = np.mgrid[:4, :4]


class Camera:
    name = 'Some stupid camera'
    _zoom = 1.
    _kx, _ky = 1., 1.

    if platform.system() == 'Windows':
        cv_backend = cv2.CAP_DSHOW
    else:
        cv_backend = cv2.CAP_V4L

    def __init__(self, stream: cv2.VideoCapture | None, global_zoom: float, width: int, height: int):
        # capture part
        self.global_zoom, self.width, self.height = global_zoom, width, height
        self.stream = stream
        self.set_camera()
        self.image = np.zeros((height, width, 3), np.uint8)

        self.screw = np.zeros((3, 2), float)

        # render part (mostly used to visually debug)
        self.transformation_matrix = np.zeros((4, 4), float)
        self.make_transformation_matrix()
        self.projection_matrix = np.zeros((2, 4), float)
        self.make_projection_matrix()
        self.ray_matrix = np.zeros((3, 3), float)
        self.make_ray_matrix()

        # marker detection
        self.detected = None

    @classmethod
    def find(cls) -> cv2.VideoCapture | None:
        cam_port = get_available_cameras().get(cls.name)
        if cam_port is None:
            return None
        return cv2.VideoCapture(cam_port, cls.cv_backend)

    @classmethod
    def new(cls, global_zoom=1., width=1920, height=1080):
        return cls(cls.find(), global_zoom, width, height)

    def set_camera(self, global_zoom=None, width=None, height=None):
        if global_zoom is not None:
            self.global_zoom = global_zoom
        if width is not None:
            self.width = width
        if global_zoom is not None:
            self.height = height
        if self.stream is None:
            return
        video_capture_settings = {
            cv2.CAP_PROP_ZOOM: self._zoom * self.global_zoom * 100.,
            cv2.CAP_PROP_FRAME_WIDTH: self.width,
            cv2.CAP_PROP_FRAME_HEIGHT: self.height,
            cv2.CAP_PROP_FOURCC: MJPG_CODEC,
            # cv2.CAP_PROP_FPS: 30.,
        }
        for key, value in video_capture_settings.items():
            self.stream.set(key, value)

    def make_ray_matrix(self):
        zx, zy = self._kx * self._zoom * self.global_zoom, self._ky * self._zoom * self.global_zoom
        self.ray_matrix[:] = (
            (1 / self.width, -.5, 0),
            (0, 1, 0),
            (0, -.5, 1 / self.height)
        )
        self.ray_matrix[::2] /= (zx,), (-zy,)

    def make_transformation_matrix(self):
        self.transformation_matrix = np.identity(4)
        r_alpha = axle_rotation(Z, -self.screw[0, 1])
        r_beta = axle_rotation(X, -self.screw[1, 1])
        r_gamma = axle_rotation(Y, -self.screw[2, 1])
        self.transformation_matrix[:3, :3] = r_gamma @ r_beta @ r_alpha
        self.transformation_matrix[:3, 3] = self.transformation_matrix[:3, :3] @ -self.screw[:, 0]

    def make_projection_matrix(self):
        self.projection_matrix[:] = (
            (self._kx * self._zoom * self.global_zoom, 0., 0., .5),
            (0., 0., -self._ky * self._zoom * self.global_zoom, .5)
        )
        self.projection_matrix *= (self.width,), (self.height,)

    def get_opencv_camera_matrix(self):
        return np.array((
            (self._kx * self._zoom * self.global_zoom, 0, .5),
            (0., self._ky * self._zoom * self.global_zoom, .5),
            (0, 0., 1.)
        )) * ((self.width,), (self.height,), (1,))

    def read(self):
        if self.stream is None:
            return False
        return self.stream.read(self.image)[0]

    def detect(self, read=False):
        if read:
            self.read()
        self.detected = detect(self.image)
        return self.detected

    def reposition(self, detect_markers=False, read=False):
        if detect_markers or read:
            self.detect(read)

        ids, rects = self.detected
        ids = filter_table_tags(ids)

        if ids:
            obj_points = np.concatenate(tuple(BOARD_TAGS[x - 20] for x, _ in ids), axis=0)
            img_points = np.concatenate(tuple(rects[x] for _, x in ids), axis=0)
            self.screw[:] = opencv_save_my_ass(obj_points, img_points, self.get_opencv_camera_matrix())
            self.make_transformation_matrix()

    def to_real_world(self, sc_points, plane_normal=Z, plane_point=(0., 0., 0.)):
        """
        take points from the screen that belong to a known real-world plane and compute their real position
        """
        rays = mat_x(self.transformation_matrix[:3, :3].T, screen_to_ray(self.ray_matrix, sc_points))
        return self.screw[:, 0] + rays * (dot(plane_point - self.screw[:, 0], plane_normal) / dot(rays, plane_normal))[..., None]

    def detect_robots(self, blue_beacon_height=0., yellow_beacon_height=0., detect_markers=False, read=False):
        if detect_markers or read:
            self.detect(read)

        ids, rects = self.detected
        blue_robot_markers = filter(lambda x: x[0] in range(1, 6), ids)
        yellow_robot_markers = filter(lambda x: x[0] in range(6, 11), ids)

        # shapes (m1, 4, 2)
        sc_blue_rects = rects_from_ids(rects, blue_robot_markers)
        # shapes (m2, 4, 2)
        sc_yellow_rects = rects_from_ids(rects, yellow_robot_markers)

        # shapes (m1, 4, 3)
        re_blue_rects = self.to_real_world(sc_blue_rects, Z, (0., 0., ROBOT_MARKER_HEIGHT+blue_robot_markers))
        # shapes (m2, 4, 3)
        re_yellow_rects = self.to_real_world(sc_yellow_rects, Z, (0., 0., ROBOT_MARKER_HEIGHT+yellow_robot_markers))

        # shapes (m1, 2)
        blue_poses = re_intersection(re_blue_rects.swapaxes(0, 1)[[0, 2, 1, 3]])
        # shapes (m2, 2)
        yellow_poses = re_intersection(re_yellow_rects.swapaxes(0, 1)[[0, 2, 1, 3]])

        # shapes (m1, 3)
        blue_vec = re_blue_rects[:, 1] - re_blue_rects[:, 0]
        yellow_vec = re_yellow_rects[:, 1] - re_yellow_rects[:, 0]

        # shapes (m1,)
        blue_mag = np.sum(blue_vec ** 2, axis=1) ** -.5
        blue_angle = np.arccos(blue_vec[:, 0] * blue_mag) * sign(blue_vec[:, 1])
        # shapes (m2,)
        yellow_mag = np.sum(blue_vec ** 2, axis=1) ** -.5
        yellow_angle = np.arccos(yellow_vec[:, 0] * yellow_mag) * sign(yellow_vec[:, 1])

        return blue_poses, blue_angle, yellow_poses, yellow_angle


class HDProWebcamC920(Camera):
    name = 'HD Pro Webcam C920'
    linux_v4l_location = '/dev/v4l/by-id/usb-046d_HD_Pro_Webcam_C920_C7FF4D4F-video-index0'
    _kx = 237 / 310
    _ky = 16/9 * _kx


class LogitechWebcamC930e(Camera):
    name = 'Logitech Webcam C930e'
    linux_v4l_location = '/dev/v4l/by-id/usb-046d_Logitech_Webcam_C930e_BBAD036E-video-index0'
    _kx = 237 / 390
    _ky = 16/9 * _kx

    # _zoom = 1.26
    # # 1.26 is an equalizer, both camera now have the same f.o.v.
    # # Zoom calculation details:
    # # both cameras face to a wall, distance was 2.37 m
    # # project the f.o.v. on the wall, measure the width
    # # C920:  3.10 m
    # # C930e: 3.90 m
    # # 3.90 / 3.10 ~ 1.26
