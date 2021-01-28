import orjson as json

from src import schedule


def test_scheduled_tasks():
    with schedule.app.test_client() as client:
        response = client.get('/schedule/')
        assert response.status_code == 200
        reply = json.loads(response.data)
        for t in reply['tasks']:
            assert schedule.task_daily.__name__ == t['function']
            assert not t['next_run']
