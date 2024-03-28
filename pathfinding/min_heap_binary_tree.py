from typing import Optional, Callable, Generic, TypeVar
from enum import Enum

import numpy
import numpy as np


class MinHeapBinaryTree:
    """
    Google it, first link, read it.
    """

    # Table of all the values in the tree.
    values: list[int]

    # Prends une valeur dans le tableau et renvois la position
    # de cette valeur dans le tableau.
    location: np.ndarray

    def __init__(self, f, location):
        self.values = []
        self.f = f
        self.location = location

    @staticmethod
    def parent_index(index: int) -> int:
        """
        Returns the index of the current node's parent node in the
        tree based off of the current node's index.
        """
        return (index - 1) // 2

    @staticmethod
    def left_child_index(index: int) -> int:
        """
        Returns the index of the current node's left child node in the
        tree based off of the current node's index.
        """
        return 2 * index + 1

    @staticmethod
    def right_child_index(index: int) -> int:
        """
        Returns the index of the current node's right child node in the
        tree based off of the current node's index.
        """
        return 2 * index + 2

    def min(self) -> Optional[int]:
        """
        Returns the value of the smallest value stored in the tree.
        Returns nothing if the tree is empty.
        """
        if len(self.values) == 0:
            return None
        return self.values[0]

    def is_empty(self) -> bool:
        """
        Checks if the current tree is empty, ie if there are no nodes.
        """
        return len(self.values) == 0

    def push(self, value: int) -> None:
        """
        Pushes a value into the tree, whilst keeping the tree's
        useful proprieties.
        """
        self.values.append(value)
        current = len(self.values) - 1
        self.location[value] = current

        # While the current index is positive and the parent index is greater than the
        # current index (hard to read I know)
        # while current > 0 and self.comparison(self.values[self.parent_index(current)],
        #                                       self.values[current]) == Comparison.GREATER:
        self.display()
        print()
        self.update(current)
        self.display()
        print()
        print()
        print()
        print()


        assert self.guarantee_integrity()
        # while current > 0 and self.f(self.values[self.parent_index(current)]) > self.f(self.values[current]):
        #     self.values[self.parent_index(current)], self.values[current] = (
        #         self.values[current], self.values[self.parent_index(current)])
        #
        #     self.location[self.values[self.parent_index(current)]], self.location[self.values[current]] = (
        #         self.location[self.values[current]], self.location[self.values[self.parent_index(current)]])
        #
        #     current = self.parent_index(current)

        # assert all(i == self.location[n] for i, n in enumerate(self.values))

    def pop(self) -> Optional[int]:
        """
        Removes the smallest value of the tree, and returns it.
        Does nothing and returns nothing if the tree is empty.
        """
        if len(self.values) == 0:
            return None

        self.location[self.values[0]] = -1

        if len(self.values) == 1:
            return self.values.pop(0)

        # Minimum is guaranteed to return an int, because we already
        # verified that the length of the tree is non-zero.
        minimum: int = self.min()

        length: int = len(self.values)
        last_element: int = self.values.pop(length-1)

        # The first element becomes the last element.
        self.values[0] = last_element
        self.location[last_element] = 0

        # Heapify the heap.
        self.heapify()

        assert self.guarantee_integrity()

        # assert all(i == self.location[n] for i, n in enumerate(self.values))
        return minimum

    def heapify(self, index: int = 0):
        """
        Fix the tree after popping an element.
        """

        if len(self.values) <= 1:
            return

        length: int = len(self.values)

        left_index: int = self.left_child_index(index)
        right_index: int = self.right_child_index(index)

        smallest_index = index

        if left_index < length and self.f(self.values[left_index]) < self.f(self.values[smallest_index]):
            smallest_index = left_index

        if right_index < length and self.f(self.values[left_index]) < self.f(self.values[smallest_index]):
            smallest_index = right_index

        if smallest_index != index:
            # Do the switcheroo
            self.values[index], self.values[smallest_index] = (
                self.values[smallest_index], self.values[index])
            self.location[self.values[index]], self.location[self.values[smallest_index]] = (
                self.location[self.values[smallest_index]], self.location[self.values[index]])

            # Recursion baby!!
            self.heapify(smallest_index)

        assert self.guarantee_integrity()

        # assert all(i == self.location[n] for i, n in enumerate(self.values))

    def update(self, current: int):
        while current > 0 and self.f(self.values[self.parent_index(current)]) > self.f(self.values[current]):
            self.values[self.parent_index(current)], self.values[current] = (
                self.values[current], self.values[self.parent_index(current)])

            self.location[self.values[self.parent_index(current)]], self.location[self.values[current]] = (
                self.location[self.values[current]], self.location[self.values[self.parent_index(current)]])

            current = self.parent_index(current)

        # assert all(i == self.location[n] for i, n in enumerate(self.values))

    def display(self, index: int = 0, depth: int = 0) -> None:
        """
        Displays the tree. for the full tree, don't change any parameters.
        """
        if index >= len(self.values):
            return

        tabulation: str = ""
        for _ in range(depth):
            tabulation += "\t"
        print(tabulation, self.f(self.values[index]))
        self.display(self.left_child_index(index), depth + 1)
        self.display(self.right_child_index(index), depth + 1)

    def __contains__(self, item) -> bool:
        for element in self.values:
            if element == item:
                return True
        return False

    def guarantee_integrity(self) -> bool:
        return all(self.f(self.values[index]) >= self.f(self.values[self.parent_index(index)])
                   for index in range(1, len(self.values)))
