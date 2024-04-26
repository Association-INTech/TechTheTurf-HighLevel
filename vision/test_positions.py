from .camera import Camera
from .geometry import sc_intersection, render_multi_cam_cached_matrices

import numpy as np
import cv2
import time
import threading

RUNNING, FPS = range(2)
shared_vars = [True, [0.] * len(Camera.__subclasses__())]

TABLE = np.array(((
    (-1500., 0., 0.),
    (-1500., 2000., 0.),
    (1500., 2000., 0.),
    (1500., 0., 0.)
),))


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
    except Exception as e:
        shared[RUNNING] = False


def main(camera_classes: list[type[Camera]], shared, fps=20.):
    cameras = tuple(cls.new() for cls in camera_classes)

    try:
        for index, camera in enumerate(cameras):
            threading.Thread(target=cam_thread, args=(index, camera, shared, fps)).start()

        time.sleep(1.)

        while shared[RUNNING] and all(camera.stream is not None for camera in cameras):
            date = time.perf_counter()

            for camera in cameras:
                # camera.read()
                camera.reposition(detect_markers=True)
                img = np.array(camera.image)

                ids, rects = camera.detected
                if ids:
                    sc_rect_centers = sc_intersection(rects.swapaxes(0, 1)[[0, 2, 1, 3]])

                    re_rect_centers = np.int32(camera.to_real_world(sc_rect_centers))

                    for sc_p, re_p, _id in zip(sc_rect_centers, re_rect_centers, ids):
                        cv2.circle(camera.image, np.int32(sc_p), 3, (192, 0, 255), -1)
                        cv2.putText(camera.image, f'{_id[0]}: {re_p[0]:d}, {re_p[1]:d}, {re_p[2]:d}', np.int32(sc_p), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 128, 0), 2)

                rendered, = render_multi_cam_cached_matrices(camera.transformation_matrix[None, ...], camera.projection_matrix[None, ...], TABLE)
                cv2.polylines(camera.image, np.int32(rendered), True, (0, 255, 0), 3)
                cv2.imshow(camera.name, camera.image)

                # blk = cv2.inRange(camera.image, (0, 0, 0), (40, 40, 40))
                # wht = cv2.inRange(camera.image, (220, 220, 200), (255, 255, 255))
                # cv2.imshow(camera.name, 255 * blk + 120 * wht)

            print('\r', ' '.join(f'{f:.02f}' for f in shared[FPS]), end='')

            while shared[RUNNING] and time.perf_counter() - date < 1 / fps:
                shared[RUNNING] &= cv2.pollKey() != ord('q') and all(cv2.getWindowProperty(cam.name, cv2.WND_PROP_VISIBLE) > 0 for cam in cameras)
    except Exception as e:
        shared[RUNNING] = False
        # raise e


main(Camera.__subclasses__(), shared_vars)
cv2.destroyAllWindows()
