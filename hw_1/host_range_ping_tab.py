"""Написать функцию host_range_ping_tab(), возможности которой
основаны на функции из примера 2. Но в данном случае результат должен быть
итоговым по всем ip-адресам, представленным в табличном формате
(использовать модуль tabulate).
Таблица должна состоять из двух колонок и выглядеть примерно так:
Reachable
10.0.0.1
10.0.0.2

Unreachable
10.0.0.3
10.0.0.4
"""
from tabulate import tabulate
from host_range_ping import host_range_ping


def host_range_ping_tab(address, count):
    """
    Проверяет доступность сетевых узлов из заданного списка
    с выводом результата на экран в в иде таблицы
    :param address: начальный ip-адрес
    :param count: количество проверяемых адресов
    """
    reachable, unreachable = host_range_ping(address, count, False)
    print(tabulate({'Доступные узлы': reachable, 'Недоступные узлы': unreachable},
                   headers='keys', tablefmt='pipe'))


if __name__ == '__main__':

    host_range_ping_tab('8.8.8.5', 5)
