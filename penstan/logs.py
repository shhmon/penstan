from datetime import datetime
from pythonjsonlogger import json

from penstan.settings import get_settings

class JsonFormatter(json.JsonFormatter):

    def add_fields(self, log_data, record, message_dict): 
        super().add_fields(log_data, record, message_dict)
        if not log_data.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_data['timestamp'] = now
        if log_data.get('level'):
            log_data['level'] = log_data['level'].upper()
        else:
            log_data['level'] = record.levelname

def get_log_config() -> dict:
    settings = get_settings()

    return {
        "version": 1,
        "formatters": {
            "json": {
                "class": "penstan.logs.JsonFormatter"
            }
        },
        "handlers": {
            "stdout": {
                "formatter": "json",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "level": settings.LOG_LEVEL,
            }
        },
        "loggers": {
            "uvicorn.error": {
                "level": settings.LOG_LEVEL,
                "propagate": True
            },
            "uvicorn.access": {
                "level": settings.LOG_LEVEL,
                "propagate": True
            },
        },
        "root": {
            "handlers": ["stdout"],
            "level": settings.LOG_LEVEL,
            "propagate": False
        },
    }
