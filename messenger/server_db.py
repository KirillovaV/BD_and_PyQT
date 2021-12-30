"""
База данных для серверной стороны.
На стороне сервера БД содержит следующие таблицы:
a) вcе клиенты:
b) история клиентов:
c) список активных клиентов:
"""
import datetime as dt
from pprint import pprint
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from common.variables import SERVER_DB


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
        user_id = Column(String, ForeignKey('all_users.user_id'))
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
        user_id = Column(String, ForeignKey('all_users.user_id'), unique=True)
        login_time = Column(DateTime)
        ip = Column(String)
        port = Column(Integer)

        def __init__(self, user_id, login_time, ip, port):
            self.user_id = user_id
            self.ip = ip
            self.port = port
            self.login_time = login_time

    def __init__(self):
        # Подключаемся к базе
        self.engine = create_engine(SERVER_DB, echo=False, pool_recycle=7200,
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

        # Добавляем пользователя в активные
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
                                          self.ActiveUsers.port
                                          ).join(self.Users)
        return active_users.all()

    def get_all_users(self):
        """
        Получить список всех пользователей
        """
        return self.session.query(self.Users.login, self.Users.last_login).all()

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


if __name__ == '__main__':
    print('-== Инициализация БД и добавление пользователей ==-')
    db = ServerStorage()
    db.user_login('user1', 'password1', '10.0.0.1', 7777)
    db.user_login('user2', 'password2', '10.0.0.2', 8888)

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
