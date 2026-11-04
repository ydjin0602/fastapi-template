import schemathesis

from schemathesis.checks import allow_header_conformance

schema = schemathesis.pytest.from_fixture('schema_fixture')


@schema.parametrize()
async def test_api(case, live_server_url):
    # Запросы идут в живой сервер (см. live_server_url в conftest.py)
    #
    # ST205 (allow_header_conformance) отключен: starlette не объединяет методы
    # одного пути в один роут, поэтому Allow-заголовок на 405/OPTIONS неполный —
    # известный квёрк FastAPI, а не ошибка контракта
    case.call_and_validate(
        base_url=live_server_url,
        excluded_checks=[allow_header_conformance],
    )
