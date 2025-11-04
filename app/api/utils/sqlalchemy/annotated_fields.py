from datetime import UTC
from datetime import datetime
from typing import Annotated
from uuid import UUID

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import mapped_column

# FIXME: Выбери какой PK тебе больше нравится =)
integer_pk = Annotated[
    int, mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
]
big_integer_pk = Annotated[
    int, mapped_column(BigInteger, primary_key=True, nullable=False, autoincrement=True)
]
uuid_pk = Annotated[
    UUID,
    mapped_column(
        primary_key=True, nullable=False, server_default=func.gen_random_uuid()
    ),
]

dt_with_tz = Annotated[
    TIMESTAMP, mapped_column(TIMESTAMP(timezone=True), nullable=False)
]

created_at_datetime = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False),
]
updated_at_datetime = Annotated[
    datetime | None,
    mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(tz=UTC),
        nullable=True,
        server_default=func.now(),
    ),
]
deleted_at_datetime = Annotated[
    datetime | None, mapped_column(DateTime(timezone=True), nullable=True)
]
