"""
Unit-тесты для модуля client.py
"""

import os
import sys
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from client import create_presence_message, read_response
from errors import MissingFieldError
from common.variables import *


class TestClient(unittest.TestCase):
    correct_response = {
        RESPONSE: 200,
        TIME: 1,
        ALERT: 'Соединение прошло успешно'
    }
    error_response = {
        RESPONSE: 400,
        TIME: 1,
        ERROR: 'Ошибка соединения'
    }

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_create_message_ok(self):
        """Формирование стандартного сообщения"""
        test_msg = create_presence_message(user='User')
        test_msg[TIME] = 1

        self.assertEqual(test_msg, {ACTION: 'presence', TIME: 1, TYPE: 'status',
                                    USER: {'account_name': 'User', 'password': ''}})

    def test_create_message_another_user_ok(self):
        """
        Формирование сообщения с другими параметрами пользователя
        Верный результ
        """
        test_msg = create_presence_message(user='Test', password='Test')
        test_msg[TIME] = 1

        self.assertEqual(test_msg, {ACTION: PRESENCE, TIME: 1, TYPE: 'status',
                                    USER: {'account_name': 'Test', 'password': 'Test'}})

    def test_create_message_another_user_error(self):
        """
        Формирование сообщения с другими параметрами пользователя
        Неверный результат
        """
        test_msg = create_presence_message(user='Test', password='Test')
        test_msg[TIME] = 1

        self.assertNotEqual(test_msg, {ACTION: PRESENCE, TIME: 1, TYPE: 'status',
                                       USER: {'account_name': 'User', 'password': ''}})

    def test_create_message_is_dict(self):
        """
        Проверяет, является ли возвращенный объект словарем
        """
        test_msg = create_presence_message(user='test')
        self.assertIsInstance(test_msg, dict)

    def test_read_response_200(self):
        """Разбор корректного ответа сервера, успешное соединение"""
        test_resp = read_response(self.correct_response)
        self.assertEqual(test_resp, '200: Соединение прошло успешно')

    def test_read_response_400(self):
        """Разбор корректного ответа сервера, ошибка соединения"""
        test_resp = read_response(self.error_response)
        self.assertEqual(test_resp, '400: Ошибка соединения')

    def test_no_response_1(self):
        """Некорректный ответ сервера"""
        self.assertRaises(MissingFieldError, read_response, {TIME: 1, ERROR: 'Ошибка соединения'})

    def test_no_response_2(self):
        """Некорректный код ответа"""
        self.assertRaises(ValueError, read_response, {RESPONSE: 300})


if __name__ == '__main__':
    unittest.main()
