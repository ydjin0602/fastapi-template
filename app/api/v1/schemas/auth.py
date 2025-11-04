from app.api.v1.schemas.base_schema import BaseSchema


class HTTPBasicKeyCredentials(BaseSchema):
    login: str
    password: str
