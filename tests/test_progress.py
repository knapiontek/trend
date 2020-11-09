from src import flow


def test_progress():
    lst = [1, 2]
    with flow.Progress(test_progress.__name__, lst) as progress:
        progress('1')
        progress('2')


def test_empty_list():
    with flow.Progress(test_progress.__name__, []) as progress:
        pass


def test_exception(caplog):
    lst = ['1st', '2nd']
    try:
        with flow.Progress(test_progress.__name__, lst) as progress:
            progress('1st')
            raise Exception('broken iteration of list')
    except:
        assert '0.0% 1st' in caplog.text
