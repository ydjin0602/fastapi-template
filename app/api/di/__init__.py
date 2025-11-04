from dishka import make_async_container

from app.api.di.application import ApplicationProvider
from app.api.di.request import RequestProvider
from app.api.di.usecase import UsecaseProvider

DI_CONTAINER = make_async_container(
    ApplicationProvider(),
    RequestProvider(),
    UsecaseProvider(),
)
