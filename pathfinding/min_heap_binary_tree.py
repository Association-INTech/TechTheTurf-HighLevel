from typing import Optional, TypeVar


class MinHeapBinaryTree:
    values: list[int]

    def __init__(self):
        values = []

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

    def min(self) -> Optional[int]:
        """
        Returns the value of the smallest value stored in the tree.
        Returns nothing if the tree is empty.
        """
        if len(self.values) == 0:
            return None
        return self.values[0]

    def push(self, value: int) -> None:
        """
        Pushes a value into the tree, whilst keeping the tree's
        useful proprieties.
        """
        self.values.append(value)
        current = len(self.values) - 1
        while current > 0 and self.values[self.parent_index(current)] > self.values[current]:
            self.values[self.parent_index(current)], self.values[current] = (
                self.values[current], self.values[self.parent_index(current)])

            current = self.parent_index(current)

    def pop(self) -> Optional[int]:
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
        last_element: int = self.values.pop(len(self.values)-1)

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

        if left_index < length and self.values[left_index] < length:
            smallest_index = left_index

        if right_index < length and self.values[right_index] < length:
            smallest_index = right_index

        if smallest_index != index:
            # Do the switcheroo
            self.values[index], self.values[smallest_index] = (
                self.values[smallest_index], self.values[index])

            # Recursion baby!!
            self.heapify(smallest_index)

