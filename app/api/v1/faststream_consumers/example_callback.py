from faststream.confluent.annotations import KafkaMessage


async def example_callback(
    msg: KafkaMessage,
) -> None:
    """Пример faststream-консюмера события из Kafka.

    Для включения:
        1. Пропиши топик в KafkaSettings (app/config.py).
        2. Раскомментируй подписку в faststream_consumers/router.py.
        3. Выставь KAFKA__ENABLED=true.

    Зависимости из DI доступны через аннотацию FromDishka (dishka):
        from dishka import FromDishka as Depends

        async def example_callback(
            msg: KafkaMessage,
            usecase: Depends[ExampleUsecase],
        ) -> None:
            await usecase(data=msg)
    """
    raise NotImplementedError
