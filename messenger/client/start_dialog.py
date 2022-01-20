from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, qApp


class UserNameDialog(QDialog):
    """
    Диалоговое окно для выбора пользователя
    """
    def __init__(self):
        super().__init__()

        self.ok_pressed = False
        self.setWindowTitle('Подключение')
        self.setFixedSize(210, 140)

        self.name_label = QLabel('Введите имя пользователя:', self)
        self.name_label.move(10, 10)
        self.name_label.setFixedSize(150, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(190, 20)
        self.client_name.move(10, 30)

        self.pass_label = QLabel('Введите пароль:', self)
        self.pass_label.move(10, 60)
        self.pass_label.setFixedSize(150, 10)

        self.client_pass = QLineEdit(self)
        self.client_pass.setFixedSize(190, 20)
        self.client_pass.move(10, 80)
        self.client_pass.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton('Старт', self)
        self.btn_ok.move(30, 110)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(110, 110)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        if self.client_name.text() and self.client_pass.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
