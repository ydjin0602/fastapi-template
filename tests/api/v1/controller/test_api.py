import schemathesis


def get_schema():
    return schemathesis.pytest.from_fixture('schema_fixture')


schema = get_schema()


# TODO: Разобраться как это работает
@schema.parametrize()
async def test_api(case):
    case.call_and_validate()
