import os
import sqlite3

from .. import constants


def update_if_needed():
    """Updates the database if it needs to be."""
    db_file = constants.DATABASE
    if os.path.exists(db_file):
        connection = sqlite3.connect(db_file)
        try:
            connection.execute("SELECT version FROM db_version")
        except sqlite3.OperationalError:  # Table doesn't exist, version is 3.1
            connection.close()
            _update(db_file, "3.1")


def _update(db_file: str, version: str):
    """
    Updates the database from the given version to the current one.

    :param db_file: The database file.
    :param version: The version to convert from.
    """
    name, ext = os.path.splitext(db_file)
    old_db_file = f"{name}-old_{version}{ext}"
    os.rename(db_file, old_db_file)
    if os.path.exists(db_file):
        os.remove(db_file)

    with open(constants.DB_SETUP_FILE) as f:
        script = "".join(f.readlines())

    old_connection = sqlite3.connect(old_db_file)
    new_connection = sqlite3.connect(db_file)
    new_connection.executescript(script)
    if version == "3.1":
        _from_v3_1(old_connection, new_connection)


def _from_v3_1(old_connection: sqlite3.Connection, new_connection: sqlite3.Connection):
    """
    Converts from version 3.1.

    :param old_connection: Connection to old database file.
    :param new_connection: Connection to new database file.
    """
    cursor = old_connection.execute("SELECT id, path FROM images")
    for entry in cursor.fetchall():
        new_connection.execute("INSERT INTO images (id, path) VALUES (?, ?)", entry)
    new_connection.commit()
    cursor.close()

    cursor = old_connection.execute("SELECT id, label, symbol, color FROM tag_types")
    for entry in cursor.fetchall():
        new_connection.execute("INSERT INTO tag_types (id, label, symbol, color) VALUES (?, ?, ?, ?)", entry)
    new_connection.commit()
    cursor.close()

    cursor = old_connection.execute("SELECT id, label, type_id FROM tags")
    for entry in cursor.fetchall():
        new_connection.execute("INSERT INTO tags (id, label, type_id) VALUES (?, ?, ?)", entry)
    new_connection.commit()
    cursor.close()

    cursor = old_connection.execute("SELECT image_id, tag_id FROM image_tag")
    for entry in cursor.fetchall():
        new_connection.execute("INSERT INTO image_tag (image_id, tag_id) VALUES (?, ?)", entry)
    new_connection.commit()
    cursor.close()

    old_connection.close()
    new_connection.close()
