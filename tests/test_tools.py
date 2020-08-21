import src.tools


def test_list_split():
    lst = [1, 2, 3, 4, 5, 'PSLV.ARCA']

    chunks = [chunk for chunk in src.tools.list_split(lst, 5)]
    assert chunks == [[1, 2, 3, 4, 5], ['PSLV.ARCA']]

    chunks = [chunk for chunk in src.tools.list_split(lst, 3)]
    assert chunks == [[1, 2, 3], [4, 5, 'PSLV.ARCA']]
