"""
Клиентская часть:
параметры командной строки скрипта client.py <addr> [<port>]:
addr — ip-адрес сервера; port — tcp-порт на сервере, по умолчанию 7777.
"""
import argparse
import json
import threading
import logging
import log.client_log_config
from time import time, ctime, sleep
from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM
from common.utils import send_message, get_message
from common.variables import *
from decos import Log
from errors import NotDictError, MissingFieldError

client_log = logging.getLogger('client')


@Log()
def create_presence_message(user, password=''):
    """
    Функция формирует presence-сообщение
    :param user: Имя пользователя
    :param password: Пароль
    :return:
    """
    message = {
        ACTION: PRESENCE,
        TIME: time(),
        TYPE: 'status',
        USER: {
            'account_name': user,
            'password': password
        }
    }
    client_log.debug(f'Создано приветственное сообщение серверу от {user}')
    return message


@Log()
def create_user_message(account_name):
    """
    Функция формирует сообщениепользователя для отправки.
    :param account_name:
    :return:
    """
    recipient = input('Введите получателя: ')
    message_text = input('Введите сообщение: ')
    message = {
        ACTION: MSG,
        TIME: time(),
        FROM: account_name,
        TO: recipient,
        TEXT: message_text
    }
    client_log.debug(f'Создано сообщение от {account_name} для {recipient}')
    return message


@Log()
def read_user_message(client_socket, user_name):
    """
    Функция обрабатывает полученные сообщения и выводит на экран.
    :param user_name: имя текущего пользователя
    :param client_socket:
    :return:
    """
    while True:
        try:
            message = get_message(client_socket)
            client_log.info(f'Получено сообщение {message}')
            client_log.debug(f'Разбор сообщения сервера: {message}')
            if (ACTION in message and message[ACTION] == MSG
                    and TIME in message and FROM in message
                    and TEXT in message
                    and TO in message and message[TO] == user_name):
                print(f'{ctime(message[TIME])} - {message[FROM]} пишет:\n'
                      f'{message[TEXT]}')
            elif TO in message and message[TO] != user_name:
                continue
            else:
                raise ValueError

        except (OSError, ConnectionError, ConnectionAbortedError,
                ConnectionResetError, json.JSONDecodeError):
            client_log.critical('Потеряно соединение с сервером.')
            break

        except ValueError:
            client_log.error(f'Получено некорректное сообщение от сервера {message}')


@Log()
def read_response(message):
    """
    Функция принимает ответ сервера и выводит на экран
    соответствующий результат
    :param message:
    :return:
    """
    client_log.debug(f'Разбор ответа сервера: {message}')
    if 'response' in message:
        if message[RESPONSE] == 200:
            return f'200: {message[ALERT]}'
        elif message[RESPONSE] == 400:
            return f'400: {message[ERROR]}'
        else:
            raise ValueError
    raise MissingFieldError(RESPONSE)


@Log()
def get_client_settings():
    """
    Получает имя пользователя, порт и ip-адрес сервера
    из аргументов командной строки или назначает по умолчанию
    :return:
    """
    args = argparse.ArgumentParser(description='Параметры для подключения к серверу')
    args.add_argument('address', default=DEFAULT_IP, nargs='?', help='IP-адрес сервера')
    args.add_argument('port', type=int, default=DEFAULT_PORT, nargs='?',
                      help='Порт для подкючения к серверу, должен находиться в диапазоне от 1024 до 65535.')
    args.add_argument('-n', '--name', default=None, help='Имя пользователя')
    namespace = args.parse_args(argv[1:])
    connection_ip = namespace.address
    connection_port = namespace.port
    user_name = namespace.name

    if not (1024 < connection_port < 65535):
        client_log.critical(f'Неверное значение порта {connection_port}.\n'
                            f'Порт должен находиться в диапазоне от 1024 до 65535.')
        exit(1)

    return connection_ip, connection_port, user_name


@Log()
def print_help(user_name):
    """
    Выводит имя текущего пользователя и подсказку по доступным командам
    :param user_name:
    :return:
    """
    print(f'Вы работаете как {user_name}')
    print('Доступные команды:\nm/message - отправить сообщение\n'
          'h/help - вывод справки\nq/quit - выход\n')


@Log()
def get_command(client_socket, user_name):
    """
    Функция реализует интерфейс взаимодействия с пользователем.
    :param client_socket:
    :param user_name:
    :return:
    """
    while True:
        command = input('Введите команду:\n')

        if command in ['m', 'message']:
            message = create_user_message(user_name)
            send_message(client_socket, message)
            client_log.info(f'Отрправлено сообщение {message}')

        elif command in ['h', 'help']:
            print_help(user_name)

        elif command in ['q', 'quit']:
            message = {
                ACTION: EXIT,
                TIME: time(),
                FROM: user_name
            }
            send_message(client_socket, message)
            # Закрываем сокет
            sleep(1)
            client_socket.close()
            client_log.info('Завершение подключения.')
            exit()

        else:
            print('Команда не распознана, введите help для вывода подсказки.')


def run_client():
    """
    Основная функция для запуска клиентской части
    """
    client_log.info(f'Запуск клиента.')
    connection_ip, connection_port, user_name = get_client_settings()

    while not user_name:
        user_name = input('Введите имя пользователя: ')

    try:
        # Создаем сокет
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((connection_ip, connection_port))
        client_log.info(f'Соединение с сервером {connection_ip}:{connection_port}')

        # Создаем и отправляем presence-сообщение
        message = create_presence_message(user_name)
        send_message(client_socket, message)
        client_log.info(f'Отрправлено сообщение {message}')

        # Получаем и обрабатываем ответ сервера
        answer = read_response(get_message(client_socket))
        client_log.info(f'Получен ответ сервера {answer}')

    except ConnectionRefusedError:
        client_log.critical(f'Не удалось установить соединение с сервером '
                            f'{connection_ip}:{connection_port}')
        exit(1)

    except (ValueError, NotDictError):
        client_log.error(f'Неверный формат передаваемых данных.')
        exit(1)

    except MissingFieldError as err:
        client_log.error(f'Ответ сервена не содержит поля {err.missing_field}')
        exit(1)

    except json.JSONDecodeError:
        client_log.error(f'Не удалось декодировать сообщение сервера.')
        exit(1)

    else:
        in_thread = threading.Thread(target=read_user_message,
                                     args=(client_socket, user_name),
                                     daemon=True)
        in_thread.start()
        client_log.debug('Сформирован поток для приема сообщений')

        out_thread = threading.Thread(target=get_command,
                                      args=(client_socket, user_name),
                                      daemon=True)
        out_thread.start()
        client_log.debug('Сформирован поток для отправки сообщений')

        print_help(user_name)

        while True:
            sleep(0.5)
            if in_thread.is_alive() and out_thread.is_alive():
                continue
            break


if __name__ == '__main__':
    run_client()
