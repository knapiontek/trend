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
                'date-time-from': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['loop-delay', 'date-time-from']
        },
        'Exante': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'account': {'type': 'string'},
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
        'definitions': {
            'Result': {
                'type': 'object',
                'properties': {
                    'profit': {'type': 'number', 'format': 'float'},
                    'total': {'type': 'number', 'format': 'float'},
                    'volume': {'type': 'number', 'format': 'integer'}
                },
                'required': ['profit', 'total', 'volume']
            }
        },
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
            'stooq_1d_health': {'type': 'boolean'},
            'yahoo_1d_health': {'type': 'boolean'},
            'exante_1d_health': {'type': 'boolean'},
            'stooq_1d_test': {'$ref': '#/definitions/Result'},
            'yahoo_1d_test': {'$ref': '#/definitions/Result'},
            'exante_1d_test': {'$ref': '#/definitions/Result'}
        },
        'required': [
            'symbol',
            'type',
            'exchange',
            'currency',
            'name',
            'description',
            'short_symbol',
            'shortable',
            'stooq_1d_health',
            'yahoo_1d_health',
            'exante_1d_health',
            'stooq_1d_test',
            'yahoo_1d_test',
            'exante_1d_test'
        ]
    }
}

SECURITY_SCHEMA = {
    'message': 'security-schema',
    'level': 'strict',
    'rule': {
        'definitions': {
            'Result': {
                'type': 'object',
                'additionalProperties': True
            }
        },
        'type': 'object',
        'additionalProperties': True,
        'properties': {
            'symbol': {'type': 'string'},
            'timestamp': {'type': 'integer'},
            'open': {'type': 'number', 'format': 'float'},
            'close': {'type': 'number', 'format': 'float'},
            'low': {'type': 'number', 'format': 'float'},
            'high': {'type': 'number', 'format': 'float'},
            'volume': {'type': 'integer'},
            'low_score': {'type': 'integer'},
            'high_score': {'type': 'integer'},
            'valid_low_score': {'type': 'integer'},
            'valid_high_score': {'type': 'integer'},
            'test': {'$ref': '#/definitions/Result'}
        },
        'required': ['symbol',
                     'timestamp',
                     'open',
                     'close',
                     'low',
                     'high',
                     'volume',
                     'low_score',
                     'high_score',
                     'valid_low_score',
                     'valid_high_score',
                     'test']
    }
}
