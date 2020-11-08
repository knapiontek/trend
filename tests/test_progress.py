from src import progress


def test_progress():
    lst = [1, 2]
    with progress.Progress(test_progress.__name__, lst) as progrezz:
        progrezz('1')
        progrezz('2')


def test_empty_list():
    with progress.Progress(test_progress.__name__, []) as progrezz:
        pass


def test_exception(caplog):
    lst = ['1st', '2nd']
    try:
        with progress.Progress(test_progress.__name__, lst) as progrezz:
            progrezz('1st')
            raise Exception('broken iteration of list')
    except:
        assert '0.0% 1st' in caplog.text
