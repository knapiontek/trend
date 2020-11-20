from typing import List


def zigzag(s: str, numRows: int) -> str:
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


def run_zigzag():
    assert "PAHNAPLSIIGYIR" == zigzag("PAYPALISHIRING", 3)


def product(args: List) -> List:
    acc = [[i1, i2] for i1 in args[0] for i2 in args[1]]
    for arg in args[2:]:
        acc = [i1 + [i2] for i1 in acc for i2 in arg]
    return acc


def run_product():
    result = product([[1, 2], [3, 4], [5, 6]])
    expected = [[1, 3, 5], [1, 3, 6], [1, 4, 5], [1, 4, 6], [2, 3, 5], [2, 3, 6], [2, 4, 5], [2, 4, 6]]
    assert result == expected


KEYPAD = {0: [], 1: [], 2: ['A', 'B', 'C'], 3: ['D', 'E', 'F'],
          4: ['G', 'H', 'I'], 5: ['J', 'K', 'L'], 6: ['M', 'N', 'O'],
          7: ['P', 'Q', 'R', 'S'], 8: ['T', 'U', 'V'], 9: ['W', 'X', 'Y', 'Z']}


def run_keypad():
    keys = [2, 2]
    result = product([KEYPAD[k] for k in keys])
    assert [''.join(r) for r in result] == ['AA', 'AB', 'AC', 'BA', 'BB', 'BC', 'CA', 'CB', 'CC']

    keys = [2, 3]
    result = product([KEYPAD[k] for k in keys])
    assert [''.join(r) for r in result] == ['AD', 'AE', 'AF', 'BD', 'BE', 'BF', 'CD', 'CE', 'CF']

    keys = [3, 6, 8, 4]
    result = product([KEYPAD[k] for k in keys])
    assert [''.join(r) for r in result] == ['DMTG', 'DMTH', 'DMTI', 'DMUG', 'DMUH', 'DMUI', 'DMVG', 'DMVH', 'DMVI',
                                            'DNTG', 'DNTH', 'DNTI', 'DNUG', 'DNUH', 'DNUI', 'DNVG', 'DNVH', 'DNVI',
                                            'DOTG', 'DOTH', 'DOTI', 'DOUG', 'DOUH', 'DOUI', 'DOVG', 'DOVH', 'DOVI',
                                            'EMTG', 'EMTH', 'EMTI', 'EMUG', 'EMUH', 'EMUI', 'EMVG', 'EMVH', 'EMVI',
                                            'ENTG', 'ENTH', 'ENTI', 'ENUG', 'ENUH', 'ENUI', 'ENVG', 'ENVH', 'ENVI',
                                            'EOTG', 'EOTH', 'EOTI', 'EOUG', 'EOUH', 'EOUI', 'EOVG', 'EOVH', 'EOVI',
                                            'FMTG', 'FMTH', 'FMTI', 'FMUG', 'FMUH', 'FMUI', 'FMVG', 'FMVH', 'FMVI',
                                            'FNTG', 'FNTH', 'FNTI', 'FNUG', 'FNUH', 'FNUI', 'FNVG', 'FNVH', 'FNVI',
                                            'FOTG', 'FOTH', 'FOTI', 'FOUG', 'FOUH', 'FOUI', 'FOVG', 'FOVH', 'FOVI']


if __name__ == '__main__':
    run_zigzag()
    run_product()
    run_keypad()
