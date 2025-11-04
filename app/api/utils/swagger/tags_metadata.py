def get_tags_metadata() -> list[dict]:
    """Генерируем доку для тегов.

    Returns:
        list[dict]

    """

    #  FIXME: В Swagger текущего проекта интегрирован один занимательный плагин
    #   который позволяет группировать теги по родительским тегам. Можно сделать любую
    #   глубину вложенности главное придерживаться синтаксиса.
    return [
        # Client
        {
            'name': 'Client',
            'description': 'Клиентские ручки',
        },
        {
            'name': 'Client|Roles',
            'description': 'Роли пользователей',
            'parent': 'Client',
        },
        {
            'name': 'Client|Users',
            'description': 'Пользователи',
            'parent': 'Client',
        },
    ]
