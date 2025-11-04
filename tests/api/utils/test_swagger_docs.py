import pytest

from tests.consts import EXCLUDED_URL


@pytest.mark.asyncio
class TestSwaggerDocs:
    async def test_default_root_detail(self, test_client):
        open_api = await test_client.get('/openapi.json')
        response = open_api.json()

        assert response['openapi'] == '3.1.0'

        urls = response['paths']

        for url, data in urls.items():
            method = next(iter(data.keys()))

            for docs in data.values():
                assert docs['summary'], f'{method}:{url}'
                assert docs['description'], f'{method}:{url}'
                assert docs['tags'], f'{method}:{url}'
                # Чекаем, что респонс отдает схему
                responses = docs['responses']

                # Чекаем переопределенное описание
                assert 'Returns' not in docs['description'], f'{method}:{url}'
                assert 'Args' not in docs['description'], f'{method}:{url}'

                for resp in responses.values():
                    # Пропускаем по экслудед
                    if excluded_url := EXCLUDED_URL.get(method):  # noqa: SIM102
                        if url in excluded_url:
                            continue

                    if resp.get('content'):
                        for content in resp['content'].values():
                            assert content != {'schema': {}}, (
                                f'{method}:{url} не имеет схему'
                            )
