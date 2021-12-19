"""
Настройки по умолчанию
"""

DEFAULT_PORT = 7777
DEFAULT_IP = '127.0.0.1'
DEFAULT_LISTEN_ADDRESSES = ''
TIMEOUT = 0.5

MAX_PACKAGE_LENGTH = 4096
MAX_USERS = 10

ENCODING = 'utf-8'

# JIM-протокол
ACTION = 'action'
TIME = 'time'
TYPE = 'type'
TO = 'to'
FROM = 'from'
TEXT = 'message'
USER = 'user'
RESPONSE = 'response'
ALERT = 'alert'
ERROR = 'error'

# Действия (actions)
PRESENCE = 'presence'
MSG = 'msg'
EXIT = 'quit'
