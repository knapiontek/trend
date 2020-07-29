from datetime import datetime

import requests

from src import config

if __name__ == '__main__':
    channel = config.notify_channel()
    response = requests.post(channel, data=f'notify: {datetime.utcnow().isoformat()}')
    assert response.status_code == 200, response.text
