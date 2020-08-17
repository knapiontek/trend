CONFIG_SCHEMA = {
    '$ref': '#/definitions/Config',
    'definitions': {
        'Config': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'exante': {
                    '$ref': '#/definitions/Exante'
                },
                'quandl': {
                    '$ref': '#/definitions/Quandl'
                },
                'notify-run': {
                    '$ref': '#/definitions/NotifyRun'
                }
            },
            'required': [
                'exante',
                'notify-run'
            ]
        },
        'Exante': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'url': {
                    'type': 'string',
                    'format': 'uri'
                },
                'app': {
                    'type': 'string',
                    'format': 'uuid'
                },
                'shared-key': {
                    'type': 'string'
                }
            },
            'required': [
                'app',
                'shared-key',
                'url'
            ]
        },
        'Quandl': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'shared-key': {
                    'type': 'string'
                }
            },
            'required': ['shared-key']
        },
        'NotifyRun': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'channel': {
                    'type': 'string',
                    'format': 'uri'
                }
            },
            'required': [
                'channel'
            ]
        }
    }
}
