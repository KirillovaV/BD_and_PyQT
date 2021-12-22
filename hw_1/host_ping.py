"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping
будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел
должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность
с выводом соответствующего сообщения («Узел доступен», «Узел недоступен»).
При этом ip-адрес сетевого узла должен создаваться с помощью
функции ip_address().
"""
import platform
from subprocess import call, PIPE
from ipaddress import ip_address


def is_ip(addr):
    """
    Проверяет, является ли значение ip-адресом
    """
    try:
        ip = ip_address(addr)
    except ValueError:
        raise Exception('Значение не является IP-адресом')
    return ip


def host_ping(address_list, print_res=True):
    """
    Проверяет доступность сетевых узлов из заданного списка
    :param address_list: список адресов
    :param print_res: флаг, нужно ли выводить результат на экран
    :return reachable, unreachable: списки доступных и недоступных хостов
    """

    result = ('Узел доступен', 'Узел недоступен')
    reachable = []
    unreachable = []

    param = '-n' if platform.system().lower() == 'windows' else '-c'
    for address in address_list:
        try:
            address = is_ip(address)
        except Exception:
            print(f'Недопустимый IP-адрес. {address} используется как доменное имя.')

        # Проверяем доступность хоста и добавляем результат в соответствующий список
        code = call(['ping', param, '2', '-w', '1', str(address)], stdout=PIPE, stderr=PIPE)
        if code:
            unreachable.append(address)
        else:
            reachable.append(address)

        # Если необходимо, выводим результат
        if print_res:
            print(f'{address} - {result[code]}')

    # Возвращаем списки доступных и недоступных адресов
    return reachable, unreachable


if __name__ == '__main__':

    ADDRESSES = ['192.168.8.1', '8.8.8.8', 'yandex.ru', 'dfsd', '0.0.0.1', '127.0.0.1']
    host_ping(ADDRESSES)
