import abc
import re
import sqlite3
import typing as typ

from .. import utils


class DAO(abc.ABC):
    """Base class for DAO objects. It defines a 'REGEX' and a 'RINSTR' function to use in SQL queries."""
    _DEFAULT = ':memory:'

    def __init__(self, database: str = _DEFAULT):
        """Initializes this DAO using the given database.
        If nothing is specified, special ':memory:' database will be used.

        :param database: The database file to connect to.
        """
        self._database_path = database
        self._connection = sqlite3.connect(self._database_path)
        # Disable autocommit when BEGIN has been called.
        self._connection.isolation_level = None
        self._connection.create_function('REGEXP', 2, self._regexp, deterministic=True)
        self._connection.create_function('RINSTR', 2, self._rinstr, deterministic=True)
        self._connection.create_function('SIMILAR', 2, self._similarity)
        self._connection.execute('PRAGMA foreign_keys = ON')

    @property
    def database_path(self) -> str:
        return self._database_path

    def close(self):
        """Closes database connection."""
        self._connection.close()

    @staticmethod
    def _regexp(pattern: str, string: str) -> bool:
        """Implementation of REGEXP function for SQL.
        Scans through string looking for a match to the pattern.

        @note Uses re.search()

        :param pattern: The regex pattern.
        :param string: The string to search into.
        :return: True if the second argument matches the pattern.
        """
        return re.search(pattern, string) is not None

    @staticmethod
    def _rinstr(s: str, sub: str) -> int:
        """Implementation of RINSTR function for SQL.
        Returns the highest index in s where substring sub is found.

        @note Uses str.rindex()

        :param s: The string to search into.
        :param sub: The string to search for.
        :return: The index, starting at 1; 0 if the substring could not be found.
        """
        try:
            return s.rindex(sub) + 1  # SQLite string indices start from 1
        except ValueError:
            return 0

    @staticmethod
    def _similarity(hash1: typ.Optional[bytes], hash2: typ.Optional[bytes]) -> bool:
        """Indicates whether the two provided hashes are similar, based on
        Hamming distance.

        @note Uses utils.image.compare_hashes()

        :param hash1: A hash.
        :param hash2: Another hash.
        :return: True if the hashes are similar, False if not or at least one of them is None.
        """
        if hash1 is not None and hash2 is not None:
            return utils.image.compare_hashes(DAO.decode_hash(hash1), DAO.decode_hash(hash2))[2]
        return False

    @staticmethod
    def encode_hash(hash_int: int) -> bytes:
        """Encodes the given image hash into a bytes.

        :param hash_int: The images hash to encode.
        :return: The resulting bytes.
        """
        return hash_int.to_bytes(8, byteorder='big', signed=False)

    @staticmethod
    def decode_hash(hash_bytes: bytes) -> int:
        """Decode the given bytes into an image hash.

        :param hash_bytes: The bytes to decode.
        :return: The resulting int.
        """
        return int.from_bytes(hash_bytes, byteorder='big', signed=False)
