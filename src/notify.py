import requests

from src import config
from src.calendar import Calendar

if __name__ == '__main__':
    channel = config.notify_channel()
    response = requests.post(channel, data=f'notify: {Calendar.format(Calendar.utc_now())}')
    assert response.status_code == 200, f'channel: {channel} reply: {response.text}'
