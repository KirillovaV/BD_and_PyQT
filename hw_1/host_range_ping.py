"""
Написать функцию host_range_ping() для перебора
ip-адресов из заданного диапазона. Меняться должен только последний октет
каждого адреса. По результатам проверки должно выводиться
соответствующее сообщение.
"""
from host_ping import host_ping, is_ip


def host_range_ping(address, count, print_res=True):
    """
    Проверяет доступность сетевых узлов из заданного списка
    :param address: начальный ip-адрес
    :param count: количество проверяемых адресов
    :param print_res: флаг, нужно ли выводить результат на экран
    :return reachable, unreachable: списки доступных и недоступных хостов
    """
    try:
        ipv4 = is_ip(address)

        # Определяем не выходит ли количество проверяемых адресов
        # за пределы последнего октета
        last_okt = int(str(ipv4).split('.')[3])
        if last_okt + count > 255:
            count = 256 - last_okt
            print(f'Заданное количество адресов выходит за пределы октета.\n'
                  f'Будет проверено адресов: {count}')

        # Создаём список адресов
        address_list = [str(ipv4 + i) for i in range(count)]
        print(f'Идёт проверка адресов...')

        # Проверяем доступность функцией host_ping
        return host_ping(address_list, print_res)

    except Exception as err:
        print(f'{address} - {err}')


if __name__ == '__main__':

    host_range_ping('8.8.8.0', 10)
    host_range_ping('8.8.8.253', 10)
    host_range_ping('iii', 10)
