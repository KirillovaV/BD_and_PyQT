"""
Серверная часть.
Параметры командной строки:
-p <port> — TCP-порт для работы (по умолчанию использует 7777);
-a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""
import argparse
import json
import select
from time import time
from sys import argv
import logging
import log.server_log_config
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from common.utils import send_message, get_message
from common.variables import *
from decos import Log
from errors import NotDictError
from descriptors import PortDescriptor
from metaclasses import ServerVerifier

server_log = logging.getLogger('server')


class Server(metaclass=ServerVerifier):
    listen_port = PortDescriptor()

    def __init__(self, listen_addr, listen_port):
        self.listen_addr = listen_addr
        self.listen_port = listen_port

        self.clients = []
        self.messages = []

    @Log()
    def create_response(self, message, client):
        """
        Функция проверяет поля сообщения на соответствие JIM-формату
        и отправляет сообщение с кодом ответа,
        либо записывает полученное сообщение в очередь на отправку.
        :param client: сокет пользователя
        :param message: сообщение в виде словаря
        :return: ответ в виде словаря
        """
        server_log.debug(f'Формирование ответа на сообщение {message}')

        # Если получено presence-сообщение, сообщаем об успешном подключении
        if (ACTION in message and message[ACTION] == PRESENCE
                and TIME in message and USER in message
                and isinstance(message[USER], dict)):
            server_log.info(f'Принято presence-сообщение {message} '
                            f'от: {message[USER]["account_name"]}')
            response = {
                RESPONSE: 200,
                TIME: time(),
                ALERT: 'Соединение прошло успешно'
            }
            server_log.info(f'Сформировано сообщение об успешном соединении с {client}')
            send_message(client, response)
            return

        # Если получено текстовое сообщение, добавляем его в список на отправку
        if (ACTION in message and message[ACTION] == MSG
                and TIME in message and FROM in message
                and TO in message and TEXT in message):
            server_log.info(f'Принято сообщение {message} от: {message[FROM]}')
            self.messages.append(message)
            return

        if ACTION in message and message[ACTION] == EXIT:
            server_log.info(f'Клиент {client} отключился от сервера.')
            client.close()
            self.clients.remove(client)
            return

        response = {
            RESPONSE: 400,
            TIME: time(),
            ERROR: 'Ошибка соединения'
        }
        server_log.info(f'Сформировано сообщение об ошибке для клиента {client}')
        send_message(client, response)
        return

    def run_server(self):
        """
        Основная функция для запуска сервера
        """
        server_log.info('Запуск сервера.')

        # Создаём сокет и начинаем прослушивание
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind((self.listen_addr, self.listen_port))
        server_socket.settimeout(TIMEOUT)

        server_socket.listen(MAX_USERS)
        server_log.info(f'Сервер запущен. Прослушиваемые адреса: {self.listen_addr}'
                        f'Порт подключения: {self.listen_port}')

        while True:
            try:
                # Получаем данные клиента
                client, client_address = server_socket.accept()
            except OSError:
                pass
            else:
                server_log.info(f'Установлено соединение клиентом {client_address}')
                self.clients.append(client)

            # Создаём списки клиентов, ожидающих обработки
            read_lst = []
            write_lst = []
            err_lst = []
            try:
                if self.clients:
                    read_lst, write_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # Получаем сообщения пользователей
            if read_lst:
                for sending_client in read_lst:
                    try:
                        incoming_message = get_message(sending_client)
                        self.create_response(incoming_message, sending_client)

                    except json.JSONDecodeError:
                        server_log.error(f'Не удалось декодировать сообщение клиента.')

                    except (ValueError, NotDictError):
                        server_log.error(f'Неверный формат передаваемых данных.')

                    except Exception as e:
                        server_log.info(f'Клиент {sending_client.getpeername()} отключился от сервера.')
                        sending_client.close()
                        self.clients.remove(sending_client)

            # Отправляем полученные сообщения клиентам
            if self.messages and write_lst:
                message = self.messages[0]
                del self.messages[0]
                for waiting_client in write_lst:
                    try:
                        send_message(waiting_client, message)
                    except Exception as e:
                        server_log.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                        waiting_client.close()
                        self.clients.remove(waiting_client)


@Log()
def get_server_settings():
    """
    Получает IP-адрес для прослушивания и порт для работы из командной строки
    :return:
    """
    server_log.info(f'Получение IP-фдреса и порта для работы.')
    args = argparse.ArgumentParser()
    args.add_argument('-a', default=DEFAULT_LISTEN_ADDRESSES, nargs='?',
                      help='Прослушиваемый IP-адрес, по умолчанию слушает все адреса.')
    args.add_argument('-p', type=int, default=DEFAULT_PORT, nargs='?',
                      help='Номер порта, должен находиться в диапазоне от 1024 до 65535.')
    namespace = args.parse_args(argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    return listen_address, listen_port


if __name__ == '__main__':

    addr, port = get_server_settings()
    server = Server(addr, port)
    server.run_server()
