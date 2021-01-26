from collections import deque
from typing import List

from src.clazz import Clazz


def reduce_init(series: List[Clazz]):
    for s in series:
        s.candidate = []
        s.score = []


def reduce_series(series: List[Clazz], score: int) -> List[Clazz]:
    assert 1 <= score <= 8
    queue = deque(series[:2])

    for s3 in series[2:]:
        s1, s2 = queue[-2], queue[-1]

        swing_limit = (2 ** (score - 1)) / 100 * s2.close

        delta12 = s2.close - s1.close
        delta23 = s3.close - s2.close

        if delta12 > 0:
            if delta23 > 0:
                s3.candidate += [score]
                queue[-1] = s3
            elif delta23 < -swing_limit:
                s2.score += [score]
                s3.candidate += [-score]
                queue += [s3]

        if delta12 < 0:
            if delta23 < 0:
                s3.candidate += [-score]
                queue[-1] = s3
            elif delta23 > swing_limit:
                s2.score += [-score]
                s3.candidate += [score]
                queue += [s3]

    return list(queue)


def mark(series: List[Clazz]):
    reduced = series
    reduce_init(reduced)
    for score in range(1, 8):
        reduced = reduce_series(reduced, score)
