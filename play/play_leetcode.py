from typing import List, Tuple


def convert(s: str, numRows: int) -> str:
    pos = 0
    lines = [''] * numRows
    i = 0
    while pos < len(s):
        for r in range(numRows):
            if i % 2 and (r == 0 or r == numRows - 1):
                lines[r] += ''
            elif pos < len(s):
                lines[r] += s[pos]
                pos += 1
        i += 1
    return ''.join(lines)


def zigzag():
    assert "PAHNAPLSIIGYIR" == convert("PAYPALISHIRING", 3)


def product(*args) -> List[Tuple[int, int]]:
    acc = [[i1, i2] for i1 in args[0] for i2 in args[1]]
    for arg in args[2:]:
        acc = [i1 + [i2] for i1 in acc for i2 in arg]
    return acc


def run_product():
    result = product([1, 2], [3, 4], [5, 6])
    expected = [[1, 3, 5], [1, 3, 6], [1, 4, 5], [1, 4, 6], [2, 3, 5], [2, 3, 6], [2, 4, 5], [2, 4, 6]]
    assert result == expected


if __name__ == '__main__':
    zigzag()
    run_product()
