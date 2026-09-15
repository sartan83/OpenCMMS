def build_logging_config(json: bool = False) -> dict:
    formatter = 'json' if json else 'verbose'
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
            'json': {
                'class': 'pythonjsonlogger.json.JsonFormatter',
                'format': '%(levelname)s %(asctime)s %(name)s %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'formatter': formatter,
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'cmms': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
