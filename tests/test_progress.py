from src import progress


def test_progress():
    lst = [1, 2]
    with progress.Progress(test_progress.__name__, lst) as progrezz:
        progrezz('1')
        progrezz('2')
