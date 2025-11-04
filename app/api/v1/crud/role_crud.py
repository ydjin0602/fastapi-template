"""FIXME Сделано в демонстрационных целях. Удалить в боевом проекте."""

from app.api.v1.crud.base_crud import BaseCRUD
from app.api.v1.models import UserRoleModel


class RoleCRUD(BaseCRUD[UserRoleModel]):
    pass
