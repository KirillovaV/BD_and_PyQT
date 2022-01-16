"""
База данных для серверной стороны.
На стороне сервера БД содержит следующие таблицы:
a) вcе клиенты
b) история клиентов
c) список активных клиентов
d) контакты пользователей
e) история действий пользователей
"""
import datetime as dt
from pprint import pprint
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class ServerStorage:
    """
    Класс-хранилище для серверной базы данных
    """
    Base = declarative_base()

    class Users(Base):
        """
        Таблица "Все пользователи"
        """
        __tablename__ = 'all_users'

        user_id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        password = Column(String)
        last_login = Column(DateTime)

        def __init__(self, login, password):
            self.login = login
            self.password = password
            self.last_login = dt.datetime.now()

    class History(Base):
        """
        Таблица "История подключений"
        """
        __tablename__ = 'login_history'

        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('all_users.user_id'))
        login_time = Column(DateTime)
        ip = Column(String)
        port = Column(Integer)

        def __init__(self, user_id, login_time, ip, port):
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.login_time = login_time

    class ActiveUsers(Base):
        """
        Таблица "Активные пользователи"
        """
        __tablename__ = 'active_users'

        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('all_users.user_id'), unique=True)
        login_time = Column(DateTime)
        ip = Column(String)
        port = Column(Integer)

        def __init__(self, user_id, login_time, ip, port):
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.login_time = login_time

    class UsersContacts(Base):
        """
        Таблица "Контакты пользователей"
        """
        __tablename__ = 'users_contacts'

        id = Column(Integer, primary_key=True)
        user = Column(Integer, ForeignKey('all_users.user_id'))
        contact = Column(Integer, ForeignKey('all_users.user_id'))

        def __init__(self, user, contact):
            self.user = user
            self.contact = contact

    class ActionsHistory(Base):
        """
        Таблица "История действий пользователей
        """
        __tablename__ = 'actions_history'

        id = Column(Integer, primary_key=True)
        user = Column(Integer, ForeignKey('all_users.user_id'))
        sent = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, user):
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        # Подключаемся к базе
        self.engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)
        # Создаём сессию
        Session = sessionmaker(self.engine)
        self.session = Session()
        # Очищаем таблицу активных пользователей
        self.session.query(self.ActiveUsers).delete()

        self.session.commit()

    def user_login(self, name, password, ip, port):
        """
        Вход пользователя в систему
        """
        # Ищем пользователя
        result = self.session.query(self.Users).filter_by(login=name)
        now = dt.datetime.now()

        if result.count():
            # Если пользователь есть, обновляем данные
            user = result.first()
            user.last_login = now
        else:
            # Иначе создаём пользователя
            user = self.Users(name, password)
            self.session.add(user)
            self.session.commit()
            user_history = self.ActionsHistory(user.user_id)
            self.session.add(user_history)

        # Добавляем пользователя в активные
        if not self.session.query(self.ActiveUsers).filter_by(user_id=user.user_id).count():
            new_user = self.ActiveUsers(user.user_id, now, ip, port)
            self.session.add(new_user)

        # Добавляем запись в историю
        history = self.History(user.user_id, now, ip, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, name):
        """
        Выход пользователя из системы
        """
        # Находим пользователя
        result = self.session.query(self.Users).filter_by(login=name).first()
        user = self.session.query(self.ActiveUsers).filter_by(user_id=result.user_id)
        # Удаляем пользователя из активных
        user.delete()

        self.session.commit()

    def get_active_users(self):
        """
        Получить список активных пользователей
        """
        active_users = self.session.query(self.Users.login,
                                          self.ActiveUsers.ip,
                                          self.ActiveUsers.port,
                                          self.ActiveUsers.login_time
                                          ).join(self.Users)
        return active_users.all()

    def get_all_users(self):
        """
        Получить список всех пользователей
        """
        users = self.session.query(self.Users.login, self.Users.last_login).all()
        return [user[0] for user in users]

    def get_login_history(self, name=None):
        """
        Получить историю входа пользователя
        По-умолчанию всех пользователей
        """
        history = self.session.query(self.Users.login,
                                     self.History.ip,
                                     self.History.port,
                                     self.History.login_time
                                     ).join(self.Users)
        if name:
            history = history.filter(self.Users.login == name)
        return history.all()

    def update_actions_history(self, sender, recipient):
        """
        Обновляет статистику отправленных/полученных сообщений пользлвателя
        """
        # Находим отправителя и получателя
        sender = self.session.query(self.Users).filter_by(login=sender).first()
        recipient = self.session.query(self.Users).filter_by(login=recipient).first()

        # Если неверный получатель выходим
        if not recipient:
            return

        # Увеличиваем счётчики и записываем
        sender_row = self.session.query(self.ActionsHistory).filter_by(user=sender.user_id).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.ActionsHistory).filter_by(user=recipient.user_id).first()
        recipient_row.accepted += 1
        self.session.commit()

    def get_actions_history(self):
        """
        Получить статистику пользователя
        """
        query = self.session.query(self.Users.login,
                                   self.Users.last_login,
                                   self.ActionsHistory.sent,
                                   self.ActionsHistory.accepted
                                   ).join(self.Users)
        return query.all()

    def add_contact(self, user, contact):
        """
        Добавить контакт
        """
        # Находим пользователей
        user = self.session.query(self.Users).filter_by(login=user).first()
        contact = self.session.query(self.Users).filter_by(login=contact).first()

        # Проверяем возможность создать контакт
        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.user_id,
                                                                           contact=contact.user_id).count():
            return

        contact_row = self.UsersContacts(user.user_id, contact.user_id)
        self.session.add(contact_row)
        self.session.commit()

    def delete_contact(self, user, contact):
        """
        Удалить контакт
        """
        user = self.session.query(self.Users).filter_by(login=user).first()
        contact = self.session.query(self.Users).filter_by(login=contact).first()

        if not contact:
            return

        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.user_id,
            self.UsersContacts.contact == contact.user_id).delete()
        self.session.commit()

    def get_user_contacts(self, user):
        """
        Влзвращает список контактов указанного пользователя
        """
        # Ищем пользователя
        user = self.session.query(self.Users).filter_by(login=user).first().user_id

        # Запрашиваем его список контактов
        query = self.session.query(self.UsersContacts,
                                   self.Users.login).filter_by(user=user).\
            join(self.Users, self.UsersContacts.contact == self.Users.user_id)

        contacts = [contact[1] for contact in query.all()]
        return contacts


if __name__ == '__main__':
    print('-== Инициализация БД и добавление пользователей ==-')
    db = ServerStorage('server_base.db3')
    db.user_login('user1', 'password1', '10.0.0.1', 7777)
    db.user_login('user2', 'password2', '10.0.0.2', 8888)
    db.user_login('user6', 'pass', '10.0.0.8', 8080)

    print('-== Активные пользователи ==-')
    print(db.get_active_users())
    print('-' * 20)
    print('-== Отключение пользователя ==-')
    db.user_logout('user1')
    print('- Все пользователи -')
    pprint(db.get_all_users())
    print('- Активные пользователи -')
    pprint(db.get_active_users())
    print('-' * 20)
    print('-== История пользователей ==-')
    pprint(db.get_login_history('user1'))
    print('-' * 20)
    pprint(db.get_login_history())

    print('-== История сообщений ==-')
    db.update_actions_history('user1', 'user2')
    db.update_actions_history('user1', 'user2')
    db.update_actions_history('user2', 'user1')

    pprint(db.get_actions_history())

    print('-== Контакты ==-')
    db.add_contact('user1', 'user2')
    db.add_contact('user1', 'user3')
    print(db.get_user_contacts('user1'))
    db.add_contact('user2', 'user6')
    print(db.get_user_contacts('user2'))
    db.delete_contact('user1', 'user2')
    print(db.get_user_contacts('user1'))

    print(db.get_all_users())
