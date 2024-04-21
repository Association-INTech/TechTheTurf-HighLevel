import numpy as np
from geometry import axle_rotation, X, Y, Z, opencv_save_my_ass, screen_to_ray, dot, mat_x
from aruco import detect, BOARD_TAGS, filter_table_tags
import cv2
import platform

# MJPG_CODEC = cv2.VideoWriter_fourcc(*'MJPG')
MJPG_CODEC = 1196444237  # Hardcoded value so that pycharm shuts the f@#k up
# Pycharm can't find any documentation about VideoWriter_fourcc

if platform.system() == 'Windows':
    from pygrabber.dshow_graph import FilterGraph

    def get_available_cameras():
        devices = FilterGraph().get_input_devices()
        return dict(map(lambda x: x[::-1], enumerate(devices)))


I, J = np.mgrid[:4, :4]


class Camera:
    name = 'Some stupid camera'
    _zoom = 1.
    _kx, _ky = 1., 1.

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

    @classmethod
    def find(cls) -> cv2.VideoCapture | None:
        cam_port = get_available_cameras().get(cls.name)
        if cam_port is None:
            return None
        return cv2.VideoCapture(cam_port, cv2.CAP_DSHOW)

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
            cv2.CAP_PROP_FOURCC: MJPG_CODEC,
            cv2.CAP_PROP_FRAME_WIDTH: self.width,
            cv2.CAP_PROP_FRAME_HEIGHT: self.height
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

    def reposition(self, img):
        ids, rects = detect(img)
        ids = filter_table_tags(ids)

        obj_points = np.concatenate(tuple(BOARD_TAGS[x - 20] for x in ids), axis=0)
        img_points = np.concatenate(tuple(rects[ids[x]] for x in ids), axis=0)
        self.screw[:] = opencv_save_my_ass(obj_points, img_points, self.get_opencv_camera_matrix())
        self.make_transformation_matrix()

    def to_real_world(self, sc_points, plane_normal=Z, plane_point=(0., 0., 0.)):
        """
        take points from the screen that belong to a known real-world plane and compute their real position
        """
        rays = mat_x(self.transformation_matrix[:3, :3].T, screen_to_ray(self.ray_matrix, sc_points))
        return self.screw + rays * dot(plane_point - self.screw[:, 0], plane_normal) / dot(rays, plane_normal)


class HDProWebcamC920(Camera):
    name = 'HD Pro Webcam C920'
    _kx = 237 / 310
    _ky = 16/9 * _kx


class LogitechWebcamC930e(Camera):
    name = 'Logitech Webcam C930e'
    _kx = 237 / 390
    _ky = 16/9 * _kx

    _zoom = 1.26
    # 1.26 is an equalizer, both camera now have the same f.o.v.
    # Zoom calculation details:
    # both cameras face to a wall, distance was 2.37 m
    # project the f.o.v. on the wall, measure the width
    # C920:  3.10 m
    # C930e: 3.90 m
    # 3.90 / 3.10 ~ 1.26