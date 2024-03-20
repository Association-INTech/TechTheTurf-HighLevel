from typing import Optional, TypeVar


class MinHeapBinaryTree:
    values: list[int]

    def __init__(self):
        values = []

    @staticmethod
    def parent_index(index: int) -> int:
        return int((index - 1) / 2)

    @staticmethod
    def left_child_index(index: int) -> int:
        return 2 * index + 1

    @staticmethod
    def right_child_index(index: int) -> int:
        return 2 * index + 2

    def min(self) -> int:
        return self.values[0]

    def push(self, value: int) -> None:
        self.values.append(value)
        current = len(self.values) - 1
        while current > 0 and self.values[self.parent_index(current)] > self.values[current]:
            self.values[self.parent_index(current)], self.values[current] = (
                self.values[current], self.values[self.parent_index(current)])

            current = self.parent_index(current)
