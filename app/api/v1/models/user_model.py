"""FIXME Сделано в демонстрационных целях. Удалить в боевом проекте."""

import typing as t

from sqlalchemy import ForeignKey
from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.api.utils.sqlalchemy.annotated_fields import created_at_datetime
from app.api.utils.sqlalchemy.annotated_fields import integer_pk
from app.api.utils.sqlalchemy.annotated_fields import updated_at_datetime
from app.api.utils.sqlalchemy.base_db_model import BaseDBModel

if t.TYPE_CHECKING:
    pass


class UserModel(BaseDBModel):
    __tablename__ = 'template_user'

    id: Mapped[integer_pk]
    user_name: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        comment='Имя юзера',  # Уникальный индекс
    )
    role_id: Mapped[int | None] = mapped_column(
        ForeignKey('template_schema.template_user_role.id', ondelete='SET NULL'),
        nullable=True,
        server_default=text('1'),
        comment='ФК на роль',
    )

    created_at: Mapped[created_at_datetime]
    updated_at: Mapped[updated_at_datetime]
