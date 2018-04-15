#!C:\ProgramData\Anaconda3\python.exe
import sqlite3
import sys

import config
from app.data_access import ImageDao

print("Image Library v" + config.VERSION)
print("SQLite v" + sqlite3.sqlite_version + " - PySQLite v" + sqlite3.version)
print()

dao = ImageDao(config.DATABASE)
# noinspection PyProtectedMember
connection = dao._connection

while True:
    sys.stdout.write("SQL> ")
    sys.stdout.flush()
    cmd = input().strip()

    if cmd == "exit":
        break

    try:
        results = connection.execute(cmd).fetchall()
        if cmd.startswith("select"):
            i = 0
            if len(results) == 0:
                print("No results")
            else:
                results_nb = len(results)
                print(str(results_nb) + " result" + ("s" if results_nb > 1 else ""))
                for result in results:
                    if i == 20:
                        print("Display more? (Y/N)")
                        sys.stdout.write("?> ")
                        sys.stdout.flush()
                        if input().upper() != "Y":
                            break
                    print("|".join(map(str, result)))
                    i += 1
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        print("\033[31mError:")
        print(str(e) + "\033[0m")

dao.close()
