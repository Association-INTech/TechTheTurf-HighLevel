from typing import Optional, Callable, Generic, TypeVar
from enum import Enum

T = TypeVar("T")


class Comparison(Enum):
    LESS = 0,
    EQUAL = 1,
    GREATER = 2

    @classmethod
    def from_int(cls, lhs: int, rhs: int):
        if lhs < rhs:
            return Comparison.LESS
        if lhs == rhs:
            return Comparison.EQUAL
        if lhs > rhs:
            return Comparison.GREATER


class MinHeapBinaryTree(Generic[T]):
    """
    Google it, first link, read it.
    """

    # Table of all the values in the tree.
    values: list[T]

    # Comparison function, evaluates to true if the first
    # parameter is greater than the
    comparison: Callable[[T, T], Comparison]

    def __init__(self, comparison: Callable[[T, T], Comparison]):
        self.values = []
        self.comparison = comparison

    @staticmethod
    def parent_index(index: int) -> int:
        """
        Returns the index of the current node's parent node in the
        tree based off of the current node's index.
        """
        return int((index - 1) / 2)

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

    def min(self) -> Optional[T]:
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

    def push(self, value: T) -> None:
        """
        Pushes a value into the tree, whilst keeping the tree's
        useful proprieties.
        """
        self.values.append(value)
        current = len(self.values) - 1
        # While the current index is positive and the parent index is greater than the
        # current index (hard to read I know)
        while current > 0 and self.comparison(self.values[self.parent_index(current)],
                                              self.values[current]) == Comparison.GREATER:
            self.values[self.parent_index(current)], self.values[current] = (
                self.values[current], self.values[self.parent_index(current)])

            current = self.parent_index(current)

    def pop(self) -> Optional[T]:
        """
        Removes the smallest value of the tree, and returns it.
        Does nothing and returns nothing if the tree is empty.
        """
        if len(self.values) == 0:
            return None

        # Minimum is guaranteed to return an int, because we already
        # verified that the length of the tree is non-zero.
        minimum: int = self.min()

        length: int = len(self.values)
        last_element: int = self.values.pop(length-1)

        # The first element becomes the last element.
        self.values[0] = last_element

        # Heapify the heap.
        self.heapify(0)

        return minimum

    def heapify(self, index: int):
        """
        Fix the tree after popping an element.
        """
        if len(self.values) <= 1:
            return

        length: int = len(self.values)

        left_index: int = self.left_child_index(index)
        right_index: int = self.right_child_index(index)

        smallest_index = index

        if left_index < length and self.comparison(self.values[left_index],
                                                   self.values[index]) == Comparison.LESS:
            smallest_index = left_index

        if right_index < length and self.comparison(self.values[right_index],
                                                    self.values[index]) == Comparison.LESS:
            smallest_index = right_index

        if smallest_index != index:
            # Do the switcheroo
            self.values[index], self.values[smallest_index] = (
                self.values[smallest_index], self.values[index])

            # Recursion baby!!
            self.heapify(smallest_index)

