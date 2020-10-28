import requests

from src import config, tool

if __name__ == '__main__':
    channel = config.notify_channel()
    response = requests.post(channel, data=f'notify: {tool.dt_format(tool.utc_now())}')
    assert response.status_code == 200, f'channel: {channel} reply: {response.text}'
