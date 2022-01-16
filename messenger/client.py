"""
Клиентская часть:
параметры командной строки скрипта client.py <addr> [<port>]:
addr — ip-адрес сервера; port — tcp-порт на сервере, по умолчанию 7777.
"""
import argparse
import logging
from sys import argv, exit
from PyQt5.QtWidgets import QApplication
from common.variables import *
from common.decos import Log
from common.errors import ServerError
from client.client_db import ClientStorage
from client.start_dialog import UserNameDialog
from client.transport import MessengerClient
from client.main_window import ClientMainWindow

client_log = logging.getLogger('client')


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

    client_log.debug(f'Получены параметры подключения {connection_ip}:{connection_port}')

    return connection_ip, connection_port, user_name


@Log()
def main():
    """
    Основная функция для запуска клиентской части мессенджера7474747474747474747474
    """
    conn_ip, conn_port, name = get_client_settings()

    client_app = QApplication(argv)

    if not name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    client_db = ClientStorage(name)

    # Создаём подключение
    try:
        connection = MessengerClient(name, conn_ip, conn_port, client_db)
    except ServerError as error:
        print(error.text)
        exit(1)
    connection.setDaemon(True)
    connection.start()

    client_log.info(f'Запущен клиент для пользователя {name}.'
                    f'Адрес подключения: {conn_ip}, порт:{conn_port}')

    # GUI
    main_window = ClientMainWindow(client_db, connection)
    main_window.make_connection(connection)
    main_window.setWindowTitle(f'Добро пожаловать, {name}')
    client_app.exec_()

    connection.connection_shutdown()
    connection.join()


if __name__ == '__main__':
    main()
