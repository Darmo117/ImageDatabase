#!/usr/bin/python3
import os.path
import pathlib

import app


def main():
    lock_file = pathlib.Path('.lock')
    if lock_file.exists():
        print('The application is already running!')
    else:
        with lock_file.open(mode='w') as f:
            f.write(str(os.getpid()))
        try:
            app.Application.run()
        finally:
            lock_file.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
