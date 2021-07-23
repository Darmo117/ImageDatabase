#!/usr/bin/python3
"""Command-line application to interact with the database."""

import sqlite3
import sys

from app import config, constants, data_access as da

print("Image Library v" + constants.VERSION)
print(f"SQLite v{sqlite3.sqlite_version} - PySQLite v{sqlite3.version}")
print("Type 'exit' to terminate the command-line.\n")

try:
    config.load_config()
except config.ConfigError as e:
    print(e, file=sys.stderr)
    sys.exit(-1)

dao = da.ImageDao(config.CONFIG.database_path)
# noinspection PyProtectedMember
connection = dao._connection

print(f"Connection: {dao.database_path}")


def print_rows(rows: list, column_names: iter):
    """
    Prints rows in a table.

    :param rows: List of rows.
    :param column_names: Names of each column.
    """
    columns = list(zip(*([column_names] + rows)))
    column_sizes = [max([len(str(v)) for v in col]) for col in columns]
    print(*[str(v).ljust(column_sizes[i]) for i, v in enumerate(column_names)], sep=" | ")
    print(*["-" * size for size in column_sizes], sep="-+-")
    for i, row in enumerate(rows):
        print(*[str(v).ljust(column_sizes[i]) for i, v in enumerate(row)], sep=" | ")


while "User hasn't typed 'exit'":
    print("SQL>", end=" ")
    cmd = input().strip()

    if cmd.lower() == "exit":
        break

    try:
        cursor = connection.execute(cmd)
        if cursor.description is not None:
            column_names = tuple(desc[0] for desc in cursor.description)
        else:
            column_names = []
        results = cursor.fetchall()

        if cmd.startswith("select"):
            if len(results) == 0:
                print("Query returned no results")
            else:
                results_nb = len(results)
                plural = "s" if results_nb > 1 else ""
                limit = 20
                i = 0
                rows = []
                for result in results:
                    if i % limit == 0:
                        if i > 0:
                            print_rows(rows, column_names)
                            rows.clear()
                            while "User enters neither Y or N":
                                print("Display more? (Y / N)")
                                print("?>", end=" ")
                                choice = input().upper()
                                if choice.upper() == "Y":
                                    proceed = True
                                    break
                                elif choice.upper() == "N":
                                    proceed = False
                                    break
                            if not proceed:
                                break
                        upper_bound = i + limit if i + limit <= results_nb else results_nb
                        print(f"Showing result{plural} {i + 1} to {upper_bound} of {results_nb}")
                    rows.append(tuple(map(repr, result)))
                    i += 1
                else:
                    print_rows(rows, column_names)
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        print("\033[31mError:")
        print(f"{e}\033[0m")

dao.close()
