from collections import deque
from typing import List

from src import tool
from src.clazz import Clazz


def init(series: List[Clazz]) -> List[Clazz]:
    for s in series:
        s.update(tool.SECURITY_SCORE_DEFAULT)

    results = []
    for s in series:
        if s.low != s.high:  # avoid duplicates
            # assume order is (open, low, high, close) for (open < close)
            value1, value2 = (s.low, s.high) if s.close > s.open else (s.high, s.low)
            results += [Clazz(data=s, value=value1), Clazz(data=s, value=value2)]
        else:
            results += [Clazz(data=s, value=s.low)]
    return results


def limit_ratio(score: int) -> float:
    assert 1 <= score <= 8
    return (2 ** (score - 1)) / 100  # 1%, 2%, 4%, 8%, 16%, 32%, 64%, 128%


def reduce(series: List[Clazz], score: int) -> List[Clazz]:
    assert 1 <= score <= 8
    queue = deque(series[:2])

    for s3 in series[2:]:
        s1, s2 = queue[-2], queue[-1]
        limit = limit_ratio(score) * s2.value

        if s2.value < s1.value:
            if s3.value < s2.value:
                s3.data.low_score = score
                queue[-1] = s3
            elif s3.value > s2.value + limit:
                s2.data.valid_low_score = score
                s3.data.high_score = score
                queue += [s3]

        if s2.value > s1.value:
            if s3.value > s2.value:
                s3.data.high_score = score
                queue[-1] = s3
            elif s3.value < s2.value - limit:
                s2.data.valid_high_score = score
                s3.data.low_score = score
                queue += [s3]

    return list(queue)


def display(series: List[Clazz], score: int) -> List[Clazz]:
    results = []
    if score:
        assert 1 <= score <= 8
        begin = series[0]
        end = series[-1]
        results += [Clazz(begin, value=begin.open)]
        for s in series[1:-1]:
            # assume order is (open, low, high, close) for (open < close)
            if s.open < s.close:
                if score <= s.valid_low_score:
                    results += [Clazz(s, value=s.low)]
                if score <= s.valid_high_score:
                    results += [Clazz(s, value=s.high)]
            else:
                if score <= s.valid_high_score:
                    results += [Clazz(s, value=s.high)]
                if score <= s.valid_low_score:
                    results += [Clazz(s, value=s.low)]
        results += [Clazz(end, value=end.close)]
    else:
        for s in series:
            # assume order is (open, low, high, close) for (open < close)
            value1, value2 = (s.low, s.high) if s.close > s.open else (s.high, s.low)
            results += [Clazz(timestamp=s.timestamp, value=s.open),
                        Clazz(timestamp=s.timestamp, value=value1),
                        Clazz(timestamp=s.timestamp, value=value2),
                        Clazz(timestamp=s.timestamp, value=s.close)]
    return results


def calculate(series: List[Clazz]):
    reduced = init(series)
    for score in range(1, 8):
        reduced = reduce(reduced, score)
