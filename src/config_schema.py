CONFIG_SCHEMA = {
    'definitions': {
        'Config': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'exante': {
                    '$ref': '#/definitions/Exante'
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
