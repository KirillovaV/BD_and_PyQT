"""
Серверная часть.
Параметры командной строки:
-p <port> — TCP-порт для работы (по умолчанию использует 7777);
-a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""
import argparse
import json
import os
import select
import threading
import configparser
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
from server_db import ServerStorage
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, create_users_model, StatisticsWindow, create_history_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

server_log = logging.getLogger('server')

new_connection = False
conflag_lock = threading.Lock()


class Server(threading.Thread, metaclass=ServerVerifier):
    listen_port = PortDescriptor()

    def __init__(self, listen_addr, listen_port, database):
        self.listen_addr = listen_addr
        self.listen_port = listen_port
        self.socket = self._init_socket()

        self.db = database

        self.clients = []
        self.messages = []

        self.names = dict()

        super().__init__()

    def _init_socket(self):
        """
        Инициализация серверного секета
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

        return server_socket

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
        global new_connection
        server_log.debug(f'Формирование ответа на сообщение {message}')

        # Если получено presence-сообщение, сообщаем об успешном подключении
        if (ACTION in message and message[ACTION] == PRESENCE
                and TIME in message and USER in message
                and isinstance(message[USER], dict)):
            server_log.info(f'Принято presence-сообщение от: {message[USER]["account_name"]}')

            # Добавляем пользователя в базу
            if message[USER]['account_name'] not in self.names.keys():
                self.names[message[USER]['account_name']] = client
                client_ip, client_port = client.getpeername()
                self.db.user_login(message[USER]['account_name'],
                                   message[USER]['password'],
                                   client_ip, client_port)
                response = {
                    RESPONSE: 200,
                    TIME: time(),
                    ALERT: 'Соединение прошло успешно'
                }
                server_log.info(f'Сформировано сообщение об успешном соединении с {client}')
                send_message(client, response)
                with conflag_lock:
                    new_connection = True
            else:
                response = {
                    RESPONSE: 400,
                    TIME: time(),
                    ERROR: 'Имя пользователя уже занято.'
                    }
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return

        # Если получено текстовое сообщение, добавляем его в список на отправку
        elif (ACTION in message and message[ACTION] == MSG
                and TIME in message and FROM in message
                and TO in message and TEXT in message):
            server_log.info(f'Принято сообщение: {message[TEXT]}. От: {message[FROM]}')
            self.messages.append(message)

            self.db.update_actions_history(message[FROM], message[TO])
            return

        # Если пользователь запрашивает контакт-лист
        elif ACTION in message and message[ACTION] == GET_CONTACTS:
            server_log.info(f'Получен запрос списка контактов от {client}')
            contact_list = self.db.get_user_contacts(message[FROM])
            response = {
                RESPONSE: 202,
                TIME: time(),
                ALERT: contact_list
            }
            send_message(client, response)
            server_log.info(f'Клиенту {client} отправлен список контактов')

        # Если пользователь хочет добавить контакт в контакт-лист
        elif (ACTION in message and message[ACTION] == ADD_CONTACT
                and FROM in message and LOGIN in message):
            self.db.add_contact(message[FROM], message[LOGIN])

            send_message(client, {RESPONSE: 200,
                                  TIME: time()
                                  })
            server_log.info(f'Пользователь {message[LOGIN]} добавлен в список контактов пользователя {message[FROM]}')

        # Если пользователь хочет удалить контакт
        elif (ACTION in message and message[ACTION] == DEL_CONTACT
                and FROM in message and LOGIN in message):
            self.db.delete_contact(message[FROM], message[LOGIN])
            send_message(client, {RESPONSE: 200,
                                  TIME: time()
                                  })
            server_log.info(f'Пользователь {message[LOGIN]} удален из списка контактов пользователя {message[FROM]}')

        # Если получено сообщение о выходе, отключаем клиента
        elif (ACTION in message and message[ACTION] == EXIT
                and FROM in message):
            # Удаляем пользователя из активных
            self.db.user_logout(message[FROM])

            server_log.info(f'Клиент {client} отключился от сервера.')
            self.clients.remove(self.names[message[FROM]])
            self.names[message[FROM]].close()
            del self.names[message[FROM]]
            with conflag_lock:
                new_connection = True
            return

        else:
            response = {
                RESPONSE: 400,
                TIME: time(),
                ERROR: 'Некорректный запрос.'
            }
            server_log.info(f'Сформировано сообщение об ошибке для клиента {client}')
            send_message(client, response)
            return

    def run(self):
        """
        Основной цикл обработки сообщений сервером
        """
        while True:
            try:
                # Получаем данные клиента
                client, client_address = self.socket.accept()
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

                    except OSError:
                        server_log.info(f'Клиент {sending_client.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == sending_client:
                                self.db.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(sending_client)

            # Отправляем полученные сообщения клиентам
            if self.messages and write_lst:
                message = self.messages[0]
                del self.messages[0]
                for waiting_client in write_lst:
                    try:
                        send_message(waiting_client, message)
                    except (ConnectionAbortedError, ConnectionError,
                            ConnectionResetError, ConnectionRefusedError):
                        server_log.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                        self.clients.remove(self.names[message[TO]])
                        self.db.user_logout(message[TO])
                        del self.names[message[TO]]


@Log()
def get_server_settings(default_port, default_address):
    """
    Получает IP-адрес для прослушивания и порт для работы из командной строки
    :return:
    """
    server_log.info(f'Получение IP-фдреса и порта для работы.')
    args = argparse.ArgumentParser()
    args.add_argument('-a', default=default_address, nargs='?',
                      help='Прослушиваемый IP-адрес, по умолчанию слушает все адреса.')
    args.add_argument('-p', type=int, default=default_port, nargs='?',
                      help='Номер порта, должен находиться в диапазоне от 1024 до 65535.')
    namespace = args.parse_args(argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    return listen_address, listen_port


def main():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    addr, port = get_server_settings(config['SETTINGS']['Default_port'],
                                     config['SETTINGS']['Listen_Address'])
    server_db = ServerStorage(os.path.join(
        config['SETTINGS']['Database_path'],
        config['SETTINGS']['Database_file'])
    )

    server = Server(addr, port, server_db)
    server.daemon = True
    server.start()

    server_app = QApplication(argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.clients_table.setModel(create_users_model(server_db))
    main_window.clients_table.resizeColumnsToContents()
    main_window.clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.clients_table.setModel(
                create_users_model(server_db))
            main_window.clients_table.resizeColumnsToContents()
            main_window.clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = StatisticsWindow()
        stat_window.statistics_table.setModel(create_history_model(server_db))
        stat_window.statistics_table.resizeColumnsToContents()
        stat_window.statistics_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.statistics_button.triggered.connect(show_statistics)
    main_window.config_button.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    main()
