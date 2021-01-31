from collections import deque
from typing import List

from src.clazz import Clazz


def limit_ratio(score: int) -> float:
    return (2 ** (score - 1)) / 100


def reduce(series: List[Clazz], score: int) -> List[Clazz]:
    assert 1 <= score <= 8
    queue = deque(series[:2])

    def append(s):
        if s != queue[-1]:
            queue.append(s)

    for s3 in series[2:]:
        s1, s2 = queue[-2], queue[-1]

        if s2.low < s1.high:
            limit = limit_ratio(score) * s2.low
            if s3.low < s2.low:
                s3.low_score = score
                queue[-1] = s3
            elif s3.high > s2.low + limit:
                s2.valid_low_score = s2.low_score
                s3.high_score = score
                append(s3)

        if s2.high > s1.low:
            limit = limit_ratio(score) * s2.high
            if s3.high > s2.high:
                s3.high_score = score
                queue[-1] = s3
            elif s3.low < s2.high - limit:
                s2.valid_high_score = s2.high_score
                s3.low_score = score
                append(s3)

    return list(queue)


def display(series: List[Clazz], score: int):
    if score is None:
        return series
    else:
        begin = series[0]
        end = series[-1]
        results = [Clazz(begin, value=begin.open)]
        for s in series[1:-1]:
            if score <= s.valid_low_score:
                results += [Clazz(s, value=s.low)]
            if score <= s.valid_high_score:
                results += [Clazz(s, value=s.high)]
        results += [Clazz(end, value=end.close)]
        return results


def init(series: List[Clazz]) -> List[Clazz]:
    for s in series:
        s.low_score = 0
        s.high_score = 0
        s.valid_low_score = 0
        s.valid_high_score = 0
    return series


def calculate(series: List[Clazz]):
    reduced = init(series)
    for score in range(1, 8):
        reduced = reduce(reduced, score)
