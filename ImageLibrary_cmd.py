#!C:\ProgramData\Anaconda3\python.exe

"""Command-line application to interact with the database."""

import sqlite3

import app.data_access as da
import config

print("Image Library v" + config.VERSION)
print(f"SQLite v{sqlite3.sqlite_version} - PySQLite v{sqlite3.version}")
print("Type 'exit' to terminate the command-line.\n")

dao = da.ImageDao(config.DATABASE)
# noinspection PyProtectedMember
connection = dao._connection

while "User hasn't type 'exit'":
    print("SQL>", end=" ")
    cmd = input().strip()

    if cmd.lower() == "exit":
        break

    try:
        results = connection.execute(cmd).fetchall()
        if cmd.startswith("select"):
            i = 0
            if len(results) == 0:
                print("No results")
            else:
                results_nb = len(results)
                plural = "s" if results_nb > 1 else ""
                print(f"{results_nb} result{plural}")
                for result in results:
                    if i == 20:
                        while "User enters neither Y or N":
                            print("Display more? (Y / N)")
                            print("?>", end=" ")
                            choice = input().upper()
                            if choice == "Y":
                                proceed = True
                                break
                            elif choice != "N":
                                proceed = False
                                break
                        if not proceed:
                            break
                    print("|".join(map(str, result)))
                    i += 1
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        print("\033[31mError:")
        print(f"{e}\033[0m")

dao.close()
