"""
Лаунчер для windows.
Запускает сервер и 2 клиента.
"""
from subprocess import Popen, CREATE_NEW_CONSOLE


def launcher_win():
    # Список запускаемых процессов
    processes = []

    while True:
        command = input('Запустить сервер (s) / '
                        'Запустить клиенты (c) / '
                        'Закрыть все окна и выйти (q)\n')

        if command == 'q':
            for proc in processes:
                proc.kill()
            processes.clear()
            break

        elif command == 's':
            # Запустить сервер
            processes.append(Popen('python run_server.py',
                                   creationflags=CREATE_NEW_CONSOLE))

        elif command == 'c':
            # Запустить 2 клиента
            for i in range(2):
                processes.append(Popen(f'python run_client.py -n user{i} -p 12345',
                                       creationflags=CREATE_NEW_CONSOLE))


if __name__ == "__main__":
    launcher_win()
