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
                'max-grade': {'type': 'integer'}
            },
            'required': ['loop-delay', 'date-time-from', 'max-grade']
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

EXCHANGE_SCHEMA = {
    'message': 'exchange-schema',
    'level': 'strict',
    'rule': {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'symbol': {'type': 'string'},
            'type': {'type': 'string'},
            'exchange': {'type': 'string'},
            'currency': {'type': 'string'},
            'name': {'type': 'string'},
            'description': {'type': 'string'},
            'short_symbol': {'type': 'string'},
            'shortable': {'type': 'boolean'},
            'health-exante': {'type': 'boolean'},
            'health-yahoo': {'type': 'boolean'},
            'health-stooq': {'type': 'boolean'},
            'total': {'type': 'number', 'format': 'float'}
        },
        'required': ['symbol',
                     'type',
                     'exchange',
                     'currency',
                     'name',
                     'description',
                     'short_symbol',
                     'shortable',
                     'health-exante',
                     'health-yahoo',
                     'health-stooq',
                     'total']
    }
}

SECURITY_SCHEMA = {
    'message': 'security-schema',
    'level': 'strict',
    'rule': {
        'type': 'object',
        'additionalProperties': True,
        'properties': {
            'symbol': {'type': 'string'},
            'timestamp': {'type': 'integer'},
            'open': {'type': 'number', 'format': 'float'},
            'close': {'type': 'number', 'format': 'float'},
            'low': {'type': 'number', 'format': 'float'},
            'high': {'type': 'number', 'format': 'float'},
            'volume': {'type': 'integer'}
        },
        'required': ['symbol', 'timestamp', 'open', 'close', 'low', 'high', 'volume']
    }
}
