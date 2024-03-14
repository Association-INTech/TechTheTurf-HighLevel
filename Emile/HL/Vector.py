import numpy as np


class Vec2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y

    def add(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def sub(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def scale(self, scalar):
        if scalar == float("inf"):
            print("We are infinite bois")
        return Vec2(self.x * scalar, self.y * scalar)

    def norm(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def normalize(self):
        inv_norm = 1.0 / self.norm()
        return self.scale(inv_norm)

    def rotate(self, angle):
        c = np.cos(angle)
        s = np.sin(angle)
        return Vec2(
            c * self.x - s * self.y,
            s * self.x + c * self.y,
        )

    def length(self) -> float:
        return np.sqrt(self.x ** 2 + self.y ** 2)
