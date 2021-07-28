import os
import pathlib
import shutil
import sqlite3

from ._migrations import migrations
from .. import config, constants


def update_database_if_needed():
    """Updates the database if it needs to be."""
    db_file = config.CONFIG.database_path
    setup = not os.path.exists(db_file)
    connection = sqlite3.connect(db_file)
    connection.isolation_level = None

    if setup:
        with open(constants.DB_SETUP_FILE) as f:
            connection.executescript(f.read())

    try:
        cursor = connection.execute('SELECT db_version, app_version FROM version')
    except sqlite3.OperationalError:
        db_version = 0
        app_version = '3.1'
    else:
        db_version, app_version = cursor.fetchone()
        cursor.close()

    # Apply all migrations starting from the DB’s version all the way up to the current version
    for i, migration in enumerate(migrations[db_version:]):
        if i == 0:
            path = pathlib.Path(db_file)
            name, ext = os.path.splitext(path.name)
            shutil.copy(db_file, path.parent / f'{name}-old_{app_version}{ext}')
        migration.migrate(connection)

    connection.close()
