from .aruco import detect
from .camera import Camera, LogitechWebcamC930e, HDProWebcamC920, get_available_cameras

import warnings
# TODO: comment this part to debug
# SHUT UP NUMPY, let me divide by 0, just put those 'NaN' quietly; opencv may shut up too... good luck
warnings.filterwarnings('ignore')
