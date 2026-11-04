"""Тесты миграций алембика.

Медленные (поднимают PG-контейнер и гоняют миграции вверх/вниз),
поэтому помечены маркером `slow`:

- `make test` — пропускает их;
- `make test_slow` — запускает все.
"""

import pytest

from pytest_alembic.tests import test_model_definitions_match_ddl
from pytest_alembic.tests import test_single_head_revision
from pytest_alembic.tests import test_up_down_consistency
from pytest_alembic.tests import test_upgrade

pytestmark = pytest.mark.slow

__all__ = [
    'test_model_definitions_match_ddl',
    'test_single_head_revision',
    'test_up_down_consistency',
    'test_upgrade',
]
