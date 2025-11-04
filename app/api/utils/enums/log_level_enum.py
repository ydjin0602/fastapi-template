from app.api.utils.enums.base_enum import BaseENUM


class LogLevelEnum(BaseENUM):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
