import requests

from src import schedule


def test_scheduled_tasks():
    schedule.run_module(True)
    response = requests.post('schedule')
    assert response.status_code == 200
    reply = response.json()
    assert reply == dict(threads={}, tasks={})
