from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, qApp


class UserNameDialog(QDialog):
    """
    Диалоговое окно для выбора пользователя
    """
    def __init__(self):
        super().__init__()

        self.ok_pressed = False
        self.setWindowTitle('Подключение')
        self.setFixedSize(210, 93)

        self.label = QLabel('Введите имя пользователя:', self)
        self.label.move(10, 10)
        self.label.setFixedSize(150, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(190, 20)
        self.client_name.move(10, 30)

        self.btn_ok = QPushButton('Старт', self)
        self.btn_ok.move(30, 60)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(110, 60)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        if self.client_name.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
