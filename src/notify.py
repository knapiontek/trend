import requests

from src import config

if __name__ == '__main__':
    channel = config.notify_channel()
    response = requests.post(channel, data='Wait for it!')
    assert response.status_code == 200, response.text
