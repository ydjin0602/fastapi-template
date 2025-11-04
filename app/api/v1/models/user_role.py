"""FIXME Сделано в демонстрационных целях. Удалить в боевом проекте."""

import typing as t

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.api.utils.sqlalchemy.annotated_fields import created_at_datetime
from app.api.utils.sqlalchemy.annotated_fields import integer_pk
from app.api.utils.sqlalchemy.base_db_model import BaseDBModel

if t.TYPE_CHECKING:
    pass


class UserRoleModel(BaseDBModel):
    __tablename__ = 'template_user_role'

    id: Mapped[integer_pk]

    role_name: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        comment='Имя роли',  # Уникальный индекс
    )

    created_at: Mapped[created_at_datetime]
