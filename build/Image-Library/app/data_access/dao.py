import re
import sqlite3
from abc import ABC

import config


class DAO(ABC):
    def __init__(self, database=':memory:'):
        self._connection = sqlite3.connect(database)
        # Disable autocommit when BEGIN has been called.
        self._connection.isolation_level = None
        with open(config.DB_SETUP_FILE) as db_script_file:
            self._connection.executescript(db_script_file.read())

        self._connection.create_function("regexp", 2, lambda x, y: re.search(x, y) is not None)

    def close(self):
        self._connection.close()
