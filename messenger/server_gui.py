"""
Реализовать графический интерфейс для мессенджера, используя библиотеку PyQt.
Реализовать графический интерфейс администратора сервера:
* отображение списка всех клиентов;
* отображение статистики клиентов;
* настройка сервера (подключение к БД, идентификация).
"""
import sys
from PyQt5.QtWidgets import QMainWindow, QDialog, QAction, QApplication, qApp
from PyQt5.QtWidgets import QLabel, QTableView, QPushButton, QLineEdit, QFileDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    """
    Класс главного окна интерфейса сервера
    """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # кнопки
        self.refresh_button = QAction('Обновить', self)
        self.statistics_button = QAction('Статистика клиентов', self)
        self.config_button = QAction('Настройки сервера', self)
        exitAction = QAction('Выход', self)
        exitAction.triggered.connect(qApp.quit)

        # Панель инструментов
        self.toolbar = self.addToolBar('ToolBar')
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.statistics_button)
        self.toolbar.addAction(self.config_button)
        self.toolbar.addAction(exitAction)

        # Параметры окна
        self.setWindowTitle('Server Info')
        self.setFixedSize(500, 600)

        self.label = QLabel('Список подключённых клиентов:', self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 25)

        # Таблица активных клиентов
        self.clients_table = QTableView(self)
        self.clients_table.move(10, 45)
        self.clients_table.setFixedSize(480, 530)

        self.statusBar()

        self.show()


class StatisticsWindow(QDialog):
    """
    Окно статистики активности клиентов
    """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(600, 600)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнопка выхода
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 550)
        self.close_button.clicked.connect(self.close)

        # Таблица статистики
        self.statistics_table = QTableView(self)
        self.statistics_table.move(10, 10)
        self.statistics_table.setFixedSize(580, 500)

        self.show()


class ConfigWindow(QDialog):
    """
    Окно настроек сервера
    """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Параметры сервера')
        self.setFixedSize(365, 260)

        # Надпись о файле базы данных:
        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        # Строка с путём базы
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Кнопка выбора пути.
        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(275, 28)

        # Функция обработчик открытия окна выбора папки
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # Метка с именем поля файла базы данных
        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        # Метка с номером порта
        self.port_label = QLabel('Номер порта для соединений:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        # Метка с адресом для соединений
        self.ip_label = QLabel('С какого IP принимаем соединения:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        # Метка с напоминанием о пустом поле.
        self.ip_label_note = QLabel(' оставьте это поле пустым, чтобы\n принимать соединения с любых адресов.', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        # Поле для ввода ip
        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        # Кнопка сохранения настроек
        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(190, 220)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


def create_users_model(database):
    """
    Создаёт таблицу активных пользователей для отображения
    """
    user_list = database.get_active_users()
    table = QStandardItemModel()
    table.setHorizontalHeaderLabels(['Имя Клиента',
                                     'IP Адрес',
                                     'Порт',
                                     'Время подключения'])
    for row in user_list:
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False)
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        table.appendRow([user, ip, port, time])
    return table


def create_history_model(database):
    """
    Создаёт таблицу истории действий пользователей
    """
    history_list = database.get_actions_history()
    table = QStandardItemModel()
    table.setHorizontalHeaderLabels(['Имя Клиента',
                                     'Последний раз входил',
                                     'Сообщений отправлено',
                                     'Сообщений получено'])
    for row in history_list:
        user, last_seen, sent, recvd = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        sent = QStandardItem(str(sent))
        sent.setEditable(False)
        recvd = QStandardItem(str(recvd))
        recvd.setEditable(False)
        table.appendRow([user, last_seen, sent, recvd])
    return table


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.statusBar().showMessage('Statusbar Message')
    test_list = QStandardItemModel(main_window)
    test_list.setHorizontalHeaderLabels(['Имя Клиента',
                                         'IP Адрес',
                                         'Порт',
                                         'Время подключения'])
    test_list.appendRow([QStandardItem('test1'),
                         QStandardItem('192.198.0.5'),
                         QStandardItem('23544'),
                         QStandardItem('16:20:34')])
    test_list.appendRow([QStandardItem('test2'),
                         QStandardItem('192.198.0.8'),
                         QStandardItem('33245'),
                         QStandardItem('16:22:11')])
    main_window.clients_table.setModel(test_list)
    main_window.clients_table.resizeColumnsToContents()

    stat_window = StatisticsWindow()
    test_list = QStandardItemModel(stat_window)
    test_list.setHorizontalHeaderLabels(['Имя Клиента',
                                         'Последний раз входил',
                                         'Отправлено',
                                         'Получено'])
    test_list.appendRow([QStandardItem('test1'),
                         QStandardItem('Fri Dec 12 16:20:34 2020'),
                         QStandardItem('2'),
                         QStandardItem('3')])
    test_list.appendRow([QStandardItem('test2'),
                         QStandardItem('Fri Dec 12 16:23:12 2020'),
                         QStandardItem('8'),
                         QStandardItem('5')])
    stat_window.statistics_table.setModel(test_list)
    stat_window.statistics_table.resizeColumnsToContents()

    conf_window = ConfigWindow()

    app.exec_()
