from app.api.utils.enums.base_enum import BaseENUM


class EnvEnum(BaseENUM):
    LOCAL = 'LOCAL'
    DEV = 'DEV'
    TEST = 'TEST'
    PROD = 'PROD'
    PYTEST = 'PYTEST'
