"""

Everything you need is packed in the Camera interface:
 - Camera.new(): find the required camera and instance it
 - Camera.detect(): detect the Aruco markers on the cameras frame (markers are cached in Camera.detected)
 - Camera.reposition(): compute camera position according to the markers
 - Camera.to_real_world(sc_points, plane_normal, plane_point): compute real position of points on the screen
LogitechWebcamC930e and HDProWebcamC920 implement Camera
"""


from .aruco import detect
from .camera import Camera, LogitechWebcamC930e, HDProWebcamC920, get_available_cameras


import warnings
# TODO: comment this part to debug
# SHUT UP NUMPY, let me divide by 0, just put those 'NaN' quietly; opencv may shut up too... good luck
warnings.filterwarnings('ignore')
