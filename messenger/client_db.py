"""
База данных для клиентской стороны.
БД содержит следующие таблицы:
a) список контактов;
b) история сообщений.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


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
        user_mame = Column(String, unique=True)

        def __init__(self, name):
            self.user_mame = name

    class MessageHistory(Base):
        """
        История сообщений пользователя
        """
        __tablename__ = 'message_history'

        id = Column(Integer, primary_key=True)
        sender = Column(String, ForeignKey('ContactList.user_mame'))
        recipient = Column(String, ForeignKey('ContactList.user_mame'))
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




