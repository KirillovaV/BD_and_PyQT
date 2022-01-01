"""
База данных для клиентской стороны.
БД содержит следующие таблицы:
a) список контактов;
b) история сообщений.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


class ClientStorage:
    """
    Класс для клиентской базы данных
    """
    Base = declarative_base()

    class ContactList(Base):
        """
        Список контактов пользователя
        """
        __tablename__ = 'contact_list'

        id = Column(Integer, primary_key=True)
        user_name = Column(String, unique=True)

        def __init__(self, name):
            self.user_name = name

    class MessageHistory(Base):
        """
        История сообщений пользователя
        """
        __tablename__ = 'message_history'

        id = Column(Integer, primary_key=True)
        sender = Column(String)
        recipient = Column(String)
        msg_text = Column(String)
        msg_time = Column(DateTime)

        def __init__(self, sender, recipient, msg_text, msg_time):
            self.sender = sender
            self.recipient = recipient
            self.msg_text = msg_text
            self.msg_time = msg_time

    def __init__(self, name):
        self.engine = create_engine(f'sqlite:///client_{name}.db3',
                                    echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(self.engine)
        self.session = Session()

        self.session.query(self.ContactList).delete()
        self.session.commit()

    def save_message(self, sender, recipient, msg_text, msg_time):
        """
        Сохраняет сообщение
        """
        self.session.add(self.MessageHistory(sender, recipient, msg_text, msg_time))
        self.session.commit()

    def get_message_history(self, name=None):
        """
        Получает историю сообщений с пользователем или всю историю сообщений
        """
        history = self.session.query(self.MessageHistory)
        if name:
            for row in history:
                if row.sender == name or row.recipient == name:
                    print(f'От {row.sender} для {row.recipient} в {row.msg_time}\n'
                          f'{row.msg_text}\n')
        else:
            for row in history:
                print(f'От {row.sender} для {row.recipient} в {row.msg_time}\n'
                      f'{row.msg_text}\n')

    def add_users(self, contact_list):
        """
        Обновляет список контактов
        """
        self.session.query(self.ContactList).delete()
        for user in contact_list:
            self.session.add(self.ContactList(user))
        self.session.commit()

    def add_contact(self, name):
        """
        Добавляет контакт в список контактов
        """
        if not self.session.query(self.ContactList).filter_by(user_name=name).count():
            self.session.add(self.ContactList(name))
            self.session.commit()

    def del_contact(self, name):
        """
        Удаляет контакт из списка контактов
        """
        self.session.query(self.ContactList).filter_by(user_name=name).delete()
        self.session.commit()

    def get_contacts(self):
        """
        Возвращает список контактов пользователя
        """
        return [contact[0] for contact in self.session.query(self.ContactList.user_name).all()]

    def check_contact(self, contact):
        """
        Проверяет наличие пользователя в списке контактов
        """
        if self.session.query(self.ContactList).filter_by(user_name=contact).count():
            return True
        else:
            return False


if __name__ == '__main__':
    test_db = ClientStorage('test1')
    for i in ['test3', 'test4', 'test5']:
        test_db.add_contact(i)

    test_db.add_contact('test4')

    test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])

    test_db.save_message('test1', 'test2', 'тестовое сообщение', datetime.now())
    test_db.save_message('test2', 'test1', 'другое тестовое сообщение', datetime.now())
    print(test_db.get_contacts())

    print(test_db.check_contact('test1'))
    print(test_db.check_contact('test10'))

    test_db.get_message_history('test2')
    test_db.get_message_history()

    test_db.del_contact('test4')
    print(test_db.get_contacts())

