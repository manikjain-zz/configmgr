{
    'hosts': {
        'required': True,
        'type': 'list'
    },
    'auth': {
        'required': True,
        'type': 'dict',
        'schema': {
            'password': {
                'required': True,
                'type': 'string'
            },
            'host_keys_path': {
                'required': True,
                'type': 'string'
            }
        }
    },
    'file': {
        'required': False,
        'type': 'dict',
        'schema': {
            'name': {
                'required': True,
                'type': 'string'
            },
            'path': {
                'required': True,
                'type': 'string'
            },
            'content': {
                'required': True,
                'type': 'string'
            },
            'permissions': {
                'required': True,
                'type': 'dict',
                'schema': {
                    'user': {
                        'required': True,
                        'type': 'string'
                    },
                    'group': {
                        'required': True,
                        'type': 'string'
                    },
                    'access': {
                        'required': True,
                        'type': 'number'
                    }
                }
            },
            'state': {
                'required': True,
                'type': 'string'
            },
            'restart_service': {
                'required': False,
                'type': 'string'
            }
        }
    },
    'package': {
        'required': False,
        'type': 'dict',
        'schema': {
            'name': {
                'required': True,
                'type': 'list'
            },
            'state': {
                'required': True,
                'type': 'string'
            },
            'restart_service': {
                'required': False,
                'type': 'string'
            }
        }
    }
}