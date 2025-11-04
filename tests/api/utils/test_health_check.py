import random

import pytest

from httpx import AsyncClient
from starlette.status import HTTP_200_OK
from starlette.status import HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.usefixtures('test_client')
@pytest.mark.asyncio
class TestHealthCheck:
    async def test_health_check(self, test_client: AsyncClient):
        response = await test_client.get(url='/health/')
        assert response.status_code == HTTP_200_OK
        assert response.text == 'OK'

    async def test_health_check_fail(self, test_client: AsyncClient):
        method = random.choice(['POST', 'PUT', 'DELETE'])
        response = await test_client.request(method=method, url='/health/')
        assert response.status_code == HTTP_405_METHOD_NOT_ALLOWED
        assert response.json()['detail'] == 'Method Not Allowed'
