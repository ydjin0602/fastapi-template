from faststream.confluent import KafkaBroker


def faststream_router(broker: KafkaBroker) -> None:
    """Метод-роутер для подключения всех faststream-консюмеров.

    Вызывается из app/main.py при старте (только если KAFKA__ENABLED=true).

    FIXME: Kafka не нужен — удали папку faststream_consumers вместе с блоком
     в app/main.py и kafka_broker_scope из app/api/di/application.py.

    Пример подключения консюмера:
        broker.subscriber(
            config.kafka.example_topic,
            group_id=config.kafka.consumer_group,
            auto_offset_reset='earliest',
        )(example_callback)
    """
