from Vector import *

from hokuyolx import HokuyoLX

# laser = HokuyoLX()
# timestamp, scan = laser.get_dist()


def get_distance_at_angle(laser: HokuyoLX, scan, angle):
    if not laser.amin < angle < laser.amax:
        return float("inf")
    val = laser.ares * (angle - laser.amin) / (laser.amax - laser.amin)
    i = int(val)
    t = val - i

    return scan[i] + t * (scan[i + 1] - scan[i])
