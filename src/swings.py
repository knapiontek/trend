from collections import deque
from typing import List, Iterable

from src.clazz import Clazz


def init(series: List[Clazz]):
    for s in series:
        s.score = []
        s.fix = []


def reduce(series: List[Clazz], score: int) -> List[Clazz]:
    assert 1 <= score <= 8
    queue = deque(series[:2])

    for s3 in series[2:]:
        s1, s2 = queue[-2], queue[-1]

        swing_limit = (2 ** (score - 1)) / 100 * s2.value

        delta12 = s2.value - s1.value
        delta23 = s3.value - s2.value

        if delta12 > 0:
            if delta23 > 0:
                s3.score += [score]
                queue[-1] = s3
            elif delta23 < -swing_limit:
                s2.fix += [score]
                s3.score += [-score]
                queue += [s3]

        if delta12 < 0:
            if delta23 < 0:
                s3.score += [-score]
                queue[-1] = s3
            elif delta23 > swing_limit:
                s2.fix += [-score]
                s3.score += [score]
                queue += [s3]

    return list(queue)


def scores(series: List[Clazz], values: Iterable[int]):
    return [s for s in series if any(v in s.score for v in values)]


def fixes(series: List[Clazz], values: Iterable[int]):
    return [s for s in series if any(v in s.fix for v in values)]


def display(series: List[Clazz], values: Iterable[int]):
    return [s for s in series if s in (series[0], series[-1]) or any(v in s.fix for v in values)]


def calculate(series: List[Clazz]):
    reduced = series
    init(reduced)
    for score in range(1, 8):
        reduced = reduce(reduced, score)
