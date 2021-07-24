#!/usr/bin/python3
"""Command-line application to interact with the database."""

import sqlite3
import sys

from app import config, constants, data_access as da
from app.i18n import translate as _t

try:
    config.load_config()
except config.ConfigError as e:
    print(e, file=sys.stderr)
    sys.exit(-1)

print(_t('main_window.title') + ' v' + constants.VERSION)
print(f'SQLite v{sqlite3.sqlite_version} - PySQLite v{sqlite3.version}')
print(_t('SQL_console.exit_notice'))

dao = da.ImageDao(config.CONFIG.database_path)
# noinspection PyProtectedMember
connection = dao._connection

print(_t('SQL_console.connection', path=dao.database_path))


def print_rows(rows: list, column_names: iter):
    """Prints rows in a table.

    :param rows: List of rows.
    :param column_names: Names of each column.
    """
    columns = list(zip(*([column_names] + rows)))
    column_sizes = [max([len(str(v)) for v in col]) for col in columns]
    print(*[str(v).ljust(column_sizes[i]) for i, v in enumerate(column_names)], sep=' | ')
    print(*['-' * size for size in column_sizes], sep='-+-')
    for i, row in enumerate(rows):
        print(*[str(v).ljust(column_sizes[i]) for i, v in enumerate(row)], sep=' | ')


while 'user hasn’t typed "exit"':
    print('SQL>', end=' ')
    cmd = input().strip()

    if cmd.lower() == 'exit':
        break

    try:
        cursor = connection.execute(cmd)
        if cursor.description is not None:
            column_names = tuple(desc[0] for desc in cursor.description)
        else:
            column_names = []
        results = cursor.fetchall()

        if cmd.startswith('select'):
            if len(results) == 0:
                print(_t('SQL_console.no_results'))
            else:
                results_nb = len(results)
                limit = 20
                i = 0
                rows = []
                for result in results:
                    if i % limit == 0:
                        if i > 0:
                            print_rows(rows, column_names)
                            rows.clear()
                            while 'user enters neither Y or N':
                                print(_t('SQL_console.display_more'))
                                print('?>', end=' ')
                                choice = input().upper()
                                if choice.upper() == 'Y':
                                    proceed = True
                                    break
                                elif choice.upper() == 'N':
                                    proceed = False
                                    break
                            if not proceed:
                                break
                        upper_bound = i + limit if i + limit <= results_nb else results_nb
                        print(_t('SQL_console.results', start=i + 1, end=upper_bound, total=results_nb))
                    rows.append(tuple(map(repr, result)))
                    i += 1
                else:
                    print_rows(rows, column_names)
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        print('\033[31m' + _t('SQL_console.error'))
        print(f'{e}\033[0m')

print(_t('SQL_console.goodbye'))

dao.close()
