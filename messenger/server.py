"""
Серверная часть.
Параметры командной строки:
-p <port> — TCP-порт для работы (по умолчанию использует 7777);
-a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""
import argparse
import os
import configparser
import logging
from sys import argv
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from common.variables import *
from common.decos import Log
from server.core import Server
from server.server_db import ServerStorage
from server.server_gui import MainWindow

server_log = logging.getLogger('server')


@Log()
def get_server_settings(default_port, default_address):
    """
    Получает IP-адрес для прослушивания и порт для работы из командной строки
    :return: IP-адрес и порт для работы сервера
    """
    server_log.info(f'Получение IP-адреса и порта для работы.')
    args = argparse.ArgumentParser()
    args.add_argument('-a', default=default_address, nargs='?',
                      help='Прослушиваемый IP-адрес, по умолчанию слушает все адреса.')
    args.add_argument('-p', type=int, default=default_port, nargs='?',
                      help='Номер порта, должен находиться в диапазоне от 1024 до 65535.')
    namespace = args.parse_args(argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    server_log.info('Аргументы успешно загружены.')
    return listen_address, listen_port


@Log()
def config_load():
    """Парсер конфигурационного ini файла."""
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    config = config_load()
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
    server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    main_window = MainWindow(server_db, server, config)

    server_app.exec_()
    server.running = False


if __name__ == '__main__':
    main()
