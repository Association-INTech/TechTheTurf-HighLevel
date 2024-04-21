import numpy as np

import vision as vs
import cv2
import time
import sys


cam = vs.LogitechWebcamC930e.new()

while True:
    cam.read()
    sys.stdout.buffer.write(cam.image.tobytes())
