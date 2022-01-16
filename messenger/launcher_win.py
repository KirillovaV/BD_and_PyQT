"""
Лаунчер
Запускает сервер и 3 клиента
"""

from subprocess import Popen, CREATE_NEW_CONSOLE


# Запускаемые процессы
processes = []

while True:
    command = input("Запустить сервер и клиенты (s) / Закрыть все окна и выйти (q) ")

    if command == 'q':
        for proc in processes:
            proc.kill()
        processes.clear()
        break

    elif command == 's':
        # Запустить сервер
        processes.append(Popen('python server.py', creationflags=CREATE_NEW_CONSOLE))

        # Запустить 3 клиента
        for i in range(2):
            processes.append(Popen(f'python client.py -n user{i}', creationflags=CREATE_NEW_CONSOLE))
