import requests

from src import config
from src.tool import DateTime

if __name__ == '__main__':
    channel = config.notify_channel()
    response = requests.post(channel, data=f'notify: {DateTime.now().format()}')
    assert response.status_code == 200, f'channel: {channel} reply: {response.text}'
