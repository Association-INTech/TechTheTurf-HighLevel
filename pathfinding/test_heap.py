import random
import numpy as np
from working_a_star import MinHeap


def test_straight(nb_tests=20, nb_points=2000):
    for test_index in range(nb_tests):
        heap = MinHeap(np.int32([-1] * nb_points), lambda x: x)

        points = list(range(nb_points))
        random.shuffle(points)

        for pt in points:
            heap.push(pt)
            assert heap.invariant()
            assert heap.index_invariant()
        minimum = 0
        for _ in range(nb_points):
            popped = heap.extract_min()
            assert heap.invariant()
            assert heap.index_invariant()

            # Invariant check insures the minimum is out; but whatever
            assert popped == minimum
            minimum += 1

        print(f'\rStraight test: {test_index+1}/{nb_tests}', end='')
    print()


case0 = lambda x: f'({x})'
case1 = lambda x: f'{x}()'
case2 = lambda x: f'(){x}'
cases = case0, case1, case2


def random_parentheses(n):
    """
    Also known as Dyck word
    https://en.wikipedia.org/wiki/Dyck_language
    """
    result = '()'
    for _ in range(1, n):
        case = int(3 * random.random())
        result = cases[case](result)
    return result


def test_random_order(nb_tests=20, nb_points=2000):
    for test_index in range(nb_tests):
        heap = MinHeap(np.int32([-1] * nb_points), lambda x: x)

        points = list(range(nb_points))
        random.shuffle(points)

        parentheses = random_parentheses(nb_points)
        push_index = 0
        for p in parentheses:
            if p == '(':
                heap.push(points[push_index])
                assert heap.invariant()
                assert heap.index_invariant()
                push_index += 1
            elif p == ')':
                heap.extract_min()
                assert heap.invariant()
                assert heap.index_invariant()
            else:
                raise ValueError(f'What are you doing !? {repr(p)} should be a parenthesis (these are parentheses)')

        print(f'\rRandom order test: {test_index + 1}/{nb_tests}', end='')
    print()


if __name__ == '__main__':
    # For reproducibility
    random.seed(1)

    # Don't fool around with nb_points, 10_000 already takes ages because of the invariant check
    test_straight()
    test_random_order(nb_points=1_000)
