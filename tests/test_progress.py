from src import progrezz


def test_progress():
    lst = [1, 2]
    with progrezz.Progress(test_progress.__name__, lst) as progress:
        progress('1')
        progress('2')
