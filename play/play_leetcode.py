from dataclasses import dataclass
from typing import List, Any, Optional


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


def longestPalindrome(s: str) -> str:
    results = []

    for pos, _ in enumerate(s):
        length = min(pos, len(s) - pos - 1)
        size = 0
        for i in range(length + 1):
            if s[pos - i] != s[pos + i]:
                break
            size = i
        result = s[pos - size:pos + size + 1]
        if result:
            results.append(result)

    return max(results, key=len)


def run_longest_palindrome():
    s = "babad"
    result = longestPalindrome(s)
    assert result == 'bab'


def fib(num: int) -> int:
    if num <= 1:
        return num
    else:
        return fib(num - 1) + fib(num - 2)


def run_fib():
    result = fib(9)
    assert result == 34


def remove_duplicates():
    _input = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    length = len(_input)
    last = 0
    i = 1
    while i < length:
        if _input[i] != _input[last]:
            last += 1
            _input[last] = _input[i]
        i += 1
    expected = [0, 1, 2, 3, 4]
    assert expected == _input[:last + 1]


def max_profit(lst: List[int]) -> int:
    length = len(lst)
    profit = 0
    i = 1
    while i < length:
        delta = lst[i] - lst[i - 1]
        if delta > 0:
            profit += delta
        i += 1
    return profit


def run_max_profit():
    lst = [7, 1, 5, 3, 6, 4]
    result = max_profit(lst)
    expected = 7
    assert result == expected

    lst = [1, 2, 3, 4, 5]
    result = max_profit(lst)
    expected = 4
    assert result == expected


@dataclass()
class LinkedList:
    val: Any
    next: 'Optional[LinkedList]'


def linked_to_list(head: LinkedList) -> List:
    if head.next is None:
        return [head.val]
    return [head.val] + linked_to_list(head.next)


def reverse_linked_list_recursive(head: LinkedList) -> Optional[LinkedList]:
    if head.next is None:
        return head
    result = reverse_linked_list_recursive(head.next)
    head.next.next = head
    head.next = None
    return result


def reverse_linked_list_iterative(head: LinkedList) -> Optional[LinkedList]:
    prev = None
    node = head
    while node:
        _next = node.next
        node.next = prev
        prev = node
        node = _next
    return prev


def run_reverse_linked_list_recursive():
    lst = [1, 2, 3]
    head: Optional[LinkedList] = None
    for elem in reversed(lst):
        head = LinkedList(val=elem, next=head)
    output = reverse_linked_list_recursive(head)
    output_lst = linked_to_list(output)
    assert list(reversed(lst)) == output_lst


def run_reverse_linked_list_iterative():
    lst = [1, 2, 3]
    head: Optional[LinkedList] = None
    for elem in reversed(lst):
        head = LinkedList(val=elem, next=head)
    output = reverse_linked_list_iterative(head)
    output_lst = linked_to_list(output)
    assert list(reversed(lst)) == output_lst


def linked_list_partition(head: LinkedList, x: int) -> LinkedList:
    begin = begin_head = LinkedList(0, None)
    end = end_head = LinkedList(0, None)

    while head:
        if head.val <= x:
            begin.next = head
            begin = begin.next
        else:
            end.next = head
            end = end.next
        head = head.next
    begin.next = end_head.next
    end.next = None
    return begin_head.next


def run_linked_list_partition():
    lst = [1, 3, 2]
    head: Optional[LinkedList] = None
    for elem in reversed(lst):
        head = LinkedList(val=elem, next=head)
    output = linked_list_partition(head, 2)
    output_lst = linked_to_list(output)
    assert [1, 2, 3] == output_lst


if __name__ == '__main__':
    run_zigzag()
    run_product()
    run_keypad()
    run_longest_palindrome()
    run_fib()
    remove_duplicates()
    run_max_profit()
    run_reverse_linked_list_recursive()
    run_reverse_linked_list_iterative()
    run_linked_list_partition()
