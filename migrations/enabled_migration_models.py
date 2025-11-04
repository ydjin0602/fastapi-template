"""Сюда импортируем все модели, которые должны использоваться в миграциях."""

from app.api.utils.sqlalchemy.base_db_model import BaseDBModel
from app.api.v1.models import __all__ as models

__all__ = [*models, 'BaseDBModel']
