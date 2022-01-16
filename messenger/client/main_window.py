"""
Реализовать графический интерфейс пользователя на стороне клиента:
Отображение списка контактов;
Выбор чата двойным кликом на элементе списка контактов;
Добавление нового контакта в локальный список контактов;
Отображение сообщений в окне чата;
Набор сообщения в окне ввода сообщения;
Отправка введенного сообщения.
"""
import sys
import logging
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, Qt

from client.main_window_ui import Ui_MainClientWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog
sys.path.append('../')
from common.errors import ServerError

client_log = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    """
    Класс основного клиентского окна
    """
    def __init__(self, database, connection):
        super().__init__()
        self.database = database
        self.connection = connection

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        self.ui.menu_exit.triggered.connect(qApp.exit)
        self.ui.btn_send.clicked.connect(self.send_message)
        # добавить контакт
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)
        # Удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        # Дополнительные требующиеся атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # Даблклик по листу контактов отправляется в обработчик
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.contact_list_update()
        self.disable_input()
        self.show()

    def disable_input(self):
        """
        Делает поля неактивными
        """
        self.ui.label_new_message.setText('Для выбора получателя дважды кликните на нем в списке контактов.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    def update_history(self):
        """
        Функция заполняет историю сообщений с выбранным пользователем
        """
        # Получаем историю
        history = sorted(self.database.get_message_history(self.current_chat),
                         key=lambda msg: msg[2])

        # Создаём модель
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        self.history_model.clear()

        # Берём не более 20 последних записей.
        length = len(history)
        start_index = 0
        if length > 20:
            start_index = length - 20
        for i in range(start_index, length):
            msg = history[i]
            mess = QStandardItem(f'{msg[2].replace(microsecond=0)}\n'
                                 f'От {msg[0]} для {msg[1]}:\n'
                                 f'{msg[3]}')
            mess.setEditable(False)
            mess.setTextAlignment(Qt.AlignLeft)
            self.history_model.appendRow(mess)

        self.ui.list_messages.scrollToBottom()

    def select_active_user(self):
        """
        Функция обработчик двойного клика по контакту
        """
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        """
        Функция устанавливает собеседника,
        получает его историю и активирует поле ввода сообщений
        """
        self.ui.label_new_message.setText(f'Введите сообщенние для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        self.update_history()

    def contact_list_update(self):
        """
        Функция обновляет контакт лист
        """
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in contacts_list:
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_window(self):
        """
        Функция добавления контакта
        """
        global select_dialog
        select_dialog = AddContactDialog(self.connection, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        """
        Функция - обработчик добавления, сообщает серверу, обновляет таблицу и список контактов
        """
        contact = item.selector.currentText()
        self.add_contact(contact)
        item.close()

    def add_contact(self, name):
        """
        Функция добавляюет контакт в базу
        """
        try:
            self.connection.add_contact(name)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.add_contact(name)
            new_contact = QStandardItem(name)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            client_log.info(f'Успешно добавлен контакт {new_contact}')
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен.')

    def delete_contact_window(self):
        """
        Функция удаления контакта
        """
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        """
        Функция удаления контакта
        """
        selected = item.selector.currentText()
        try:
            self.connection.del_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.del_contact(selected)
            self.contact_list_update()
            client_log.info(f'Успешно удалён контакт {selected}')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            item.close()

            if selected == self.current_chat:
                self.current_chat = None
                self.disable_input()

    def send_message(self):
        """
        Функция отправки собщения пользователю.
        """
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        try:
            self.connection.create_user_message(self.current_chat, message_text)
            # pass
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.database.save_message(self.connection.user_name, self.current_chat, message_text)
            client_log.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.update_history()

    # Слот приёма нового сообщений
    @pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_chat:
            self.update_history()
        else:
            if self.database.check_contact(sender):
                # Если пользователь в контактах
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}, открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                # Если такого пользователя нет
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}.\n '
                                          f'Данного пользователя нет в вашем контакт-листе.\n'
                                          f' Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        """
        Слот потери соединения
        """
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')
        self.close()

    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from client_db import ClientStorage
    database = ClientStorage('test1')
    from transport import MessengerClient
    transport = MessengerClient('test1', '127.0.0.1', 7777, database)
    window = ClientMainWindow(database, transport)
    sys.exit(app.exec_())
