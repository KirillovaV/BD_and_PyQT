"""
Ошибки
"""


class NotDictError(Exception):
    def __str__(self):
        return 'Аргумент функции должен быть словарем'


class MissingFieldError(Exception):
    """
    Ошибка - отсутствует обязательное поле
    """
    def __init__(self, field):
        self.missing_field = field

    def __str__(self):
        return f'Отсутствует обязательное поле {self.missing_field}'


class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
