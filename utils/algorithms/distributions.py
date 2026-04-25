# used by:
import numpy as np


def random_2d(size_x: int, size_y: int, N: int, value: callable = lambda x, y, N: 1):
    r = np.zeros((size_x, size_y))
    used = []
    for i in range(N):
        x = -1
        y = -1
        while x < 0 or y < 0 or (x, y) in used:
            x = np.random.randint(0, size_x)
            y = np.random.randint(0, size_y)

        used.append((x, y))
        r[x][y] = value(x, y, i)

    return r
