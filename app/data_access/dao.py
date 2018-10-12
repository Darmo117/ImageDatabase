import os
import re
import sqlite3
from abc import ABC

from .. import constants


class DAO(ABC):
    """Base class for DAO objects. It defines a 'regex' function to use in SQL queries."""
    _DEFAULT = ":memory:"

    def __init__(self, database: str = _DEFAULT):
        """
        Initializes this DAO using the given database. If nothing is specified, special ':memory:' database will be
        used.

        :param database: The database to connect to.
        """
        file_exists = os.path.exists(database) and database != self._DEFAULT
        self._database_path = database
        self._connection = sqlite3.connect(self._database_path)
        # Disable autocommit when BEGIN has been called.
        self._connection.isolation_level = None
        if not file_exists:
            with open(constants.DB_SETUP_FILE) as db_script_file:
                self._connection.executescript(db_script_file.read())

        self._connection.create_function("regexp", 2, lambda x, y: re.search(x, y) is not None)
        self._connection.execute("PRAGMA foreign_keys = ON")

    @property
    def database_path(self) -> str:
        return self._database_path

    def close(self):
        """Closes database connection."""
        self._connection.close()
