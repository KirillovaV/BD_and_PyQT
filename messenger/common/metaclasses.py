"""
1. Реализовать метакласс ClientVerifier, выполняющий базовую проверку
класса «Клиент» (для некоторых проверок уместно использовать модуль dis):
отсутствие вызовов accept и listen для сокетов;
использование сокетов для работы по TCP;

2. Реализовать метакласс ServerVerifier, выполняющий базовую
проверку класса «Сервер»:
отсутствие вызовов connect для сокетов;
использование сокетов для работы по TCP.
"""

import dis


class ClientVerifier(type):
    """
    Класс для базовой проверки клиента
    """
    def __init__(cls, name, bases, cls_dict):
        # Методы, недопустимые к использованию в классе
        wrong_methods = ('accept', 'listen')
        methods = []
        # Запускаем цикл по функциям класса
        for func in cls_dict:
            try:
                instructions = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for i in instructions:
                    if i.opname == 'LOAD_GLOBAL':
                        # Если найден недопустимый метод, вызвать ошибку
                        if i.argval in wrong_methods:
                            raise TypeError('Использование недопустимого метода.')
                        elif i.argval not in methods:
                            methods.append(i.argval)

        # Проверяем наличие использования сокетов
        if not ('SOCK_STREAM' in methods and 'AF_INET' in methods):
            raise TypeError('Некорректная инициализация сокета.')

        super().__init__(name, bases, cls_dict)


class ServerVerifier(type):
    """
    Класс для базовой проверки сервера
    """
    def __init__(cls, name, bases, cls_dict):
        # Методы, недопустимые к использованию в классе
        wrong_methods = ('connect',)
        methods = []

        for func in cls_dict:
            try:
                instructions = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for i in instructions:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval in 'connect':
                            raise TypeError('Использование недопустимого метода.')
                        elif i.argval not in wrong_methods:
                            methods.append(i.argval)

        if not ('SOCK_STREAM' in methods and 'AF_INET' in methods):
            raise TypeError('Некорректная инициализация сокета.')

        super().__init__(name, bases, cls_dict)
