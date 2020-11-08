import orjson as json

from src import schedule


def test_scheduled_tasks():
    with schedule.app.test_client() as client:
        response = client.get('/schedule')
        assert response.status_code == 200
        reply = json.loads(response.data)
        assert schedule.maintain_task.__name__ in [t['function'] for t in reply['tasks']]
