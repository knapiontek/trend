CONFIG_SCHEMA = {
    '$ref': '#/definitions/Config',
    'definitions': {
        'Config': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'system': {'$ref': '#/definitions/System'},
                'exante': {'$ref': '#/definitions/Exante'},
                'quandl': {'$ref': '#/definitions/Quandl'},
                'iex': {'$ref': '#/definitions/IEX'},
                'notify-run': {'$ref': '#/definitions/NotifyRun'},
                'arango-db': {'$ref': '#/definitions/ArangoDB'}
            },
            'required': ['system', 'exante', 'quandl', 'iex', 'notify-run', 'arango-db']
        },
        'System': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'loop-delay': {'type': 'number', 'format': 'float'},
                'date-time-from': {'type': 'string', 'format': 'date-time'},
                'max-time-series-order': {'type': 'integer'}
            },
            'required': ['loop-delay', 'date-time-from', 'max-time-series-order']
        },
        'Exante': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'app': {'type': 'string', 'format': 'uuid'},
                'shared-key': {'type': 'string'}
            },
            'required': ['app', 'shared-key']
        },
        'Quandl': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'shared-key': {'type': 'string'}
            },
            'required': ['shared-key']
        },
        'IEX': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'shared-key': {'type': 'string'}
            },
            'required': ['shared-key']
        },
        'NotifyRun': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'channel': {'type': 'string', 'format': 'uri'}
            },
            'required': ['channel']
        },
        'ArangoDB': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'url': {'type': 'string', 'format': 'uri'},
                'username': {'type': 'string'},
                'password': {'type': 'string'},
                'database': {'type': 'string'}
            },
            'required': ['url', 'username', 'password', 'database']
        }
    }
}
