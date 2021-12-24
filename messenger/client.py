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
from metaclasses import ClientVerifier

client_log = logging.getLogger('client')


class MessengerClient(metaclass=ClientVerifier):

    def __init__(self, user_name, password, connection_ip, connection_port):
        self.user_name = user_name
        self.password = password
        self.socket = self._create_connection(connection_ip, connection_port)

    @staticmethod
    def _create_connection(ip, port):
        """
        Функция пытается установить соединение с сервером
        из полученных ip-адреса и порта
        :return: клиентский сокет
        """
        try:
            client_socket = socket(AF_INET, SOCK_STREAM)
            client_socket.connect((ip, port))
            client_log.info(f'Соединение с сервером {ip}:{port}')

        except ConnectionRefusedError:
            client_log.critical(f'Не удалось установить соединение с сервером '
                                f'{ip}:{port}')
            exit(1)
        else:
            return client_socket

    @Log()
    def get_command(self):
        """
        Функция реализует интерфейс взаимодействия с пользователем.
        """
        while True:
            command = input('Введите команду:\n')

            if command in ['m', 'message']:
                message = self.create_user_message()
                send_message(self.socket, message)
                client_log.info(f'Отрправлено сообщение {message}')

            elif command in ['h', 'help']:
                self.print_help()

            elif command in ['q', 'quit']:
                message = {
                    ACTION: EXIT,
                    TIME: time(),
                    FROM: self.user_name
                }
                try:
                    send_message(self.socket, message)
                except:
                    pass
                sleep(0.5)
                self.socket.close()
                client_log.info('Завершение подключения.')
                exit()

            else:
                print('Команда не распознана, введите help для вывода подсказки.')

    @Log()
    def print_help(self):
        """
        Выводит имя текущего пользователя и подсказку по доступным командам
        """
        print(f'Вы работаете как {self.user_name}')
        print('Доступные команды:\n'
              'm/message - отправить сообщение\n'
              'h/help - вывод справки\n'
              'q/quit - выход')

    @Log()
    def create_presence_message(self):
        """
        Функция формирует presence-сообщение для сервера
        :return:
        """
        message = {
            ACTION: PRESENCE,
            TIME: time(),
            TYPE: 'status',
            USER: {
                'account_name': self.user_name,
                'password': self.password
            }
        }
        client_log.debug(f'Создано приветственное сообщение серверу от {self.user_name}')
        return message

    @Log()
    def create_user_message(self):
        """
        Функция формирует сообщениепользователя для отправки.
        :return:
        """
        recipient = input('Введите получателя: ')
        message_text = input('Введите сообщение: ')
        message = {
            ACTION: MSG,
            TIME: time(),
            FROM: self.user_name,
            TO: recipient,
            TEXT: message_text
        }
        client_log.debug(f'Создано сообщение от {self.user_name} для {recipient}')
        return message

    @Log()
    def read_user_message(self):
        """
        Функция обрабатывает полученные сообщения и выводит на экран.
        :return:
        """
        while True:
            try:
                message = get_message(self.socket)
                client_log.info(f'Получено сообщение {message}')
                client_log.debug(f'Разбор сообщения сервера: {message}')
                if (ACTION in message and message[ACTION] == MSG
                        and TIME in message and FROM in message
                        and TEXT in message
                        and TO in message and message[TO] == self.user_name):
                    print(f'{ctime(message[TIME])} - {message[FROM]} пишет:\n'
                          f'{message[TEXT]}')
                elif TO in message and message[TO] != self.user_name:
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
    def read_response(self, message):
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

    def run_client(self):
        """
        Основная функция для запуска клиентской части
        """
        client_log.info(f'Запуск клиента.')
        try:
            # Создаем и отправляем presence-сообщение
            message = self.create_presence_message()
            send_message(self.socket, message)
            client_log.info(f'Отрправлено сообщение {message}')

            # Получаем и обрабатываем ответ сервера
            answer = self.read_response(get_message(self.socket))
            client_log.info(f'Получен ответ сервера {answer}')

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
            in_thread = threading.Thread(target=self.read_user_message,
                                         daemon=True)
            in_thread.start()
            client_log.debug('Сформирован поток для приема сообщений')

            out_thread = threading.Thread(target=self.get_command,
                                          daemon=True)
            out_thread.start()
            client_log.debug('Сформирован поток для отправки сообщений')

            user.print_help()

            while True:
                sleep(0.5)
                if in_thread.is_alive() and out_thread.is_alive():
                    continue
                break


@Log()
def get_client_settings():
    """
    Получает порт и ip-адрес сервера из аргументов командной строки
    или назначает по умолчанию
    :return:
    """
    args = argparse.ArgumentParser()
    args.add_argument('address', default=DEFAULT_IP, nargs='?')
    args.add_argument('port', type=int, default=DEFAULT_PORT, nargs='?')
    args.add_argument('-n', '--name', default=None, nargs='?')
    namespace = args.parse_args(argv[1:])
    connection_ip = namespace.address
    connection_port = namespace.port
    user_name = namespace.name

    if not (1024 < connection_port < 65535):
        client_log.critical(f'Неверное значение порта {connection_port}.\n'
                            f'Порт должен находиться в диапазоне от 1024 до 65535.')
        exit(1)

    return connection_ip, connection_port, user_name


if __name__ == '__main__':
    connection_ip, connection_port, user_name = get_client_settings()

    while not user_name:
        user_name = input('Введите имя пользователя: ')

    # user_password = input('Введите пароль: ')

    user = MessengerClient(user_name, '', connection_ip, connection_port)
    user.run_client()
