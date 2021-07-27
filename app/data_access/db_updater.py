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
        version, = connection.execute('SELECT version FROM db_version').fetchone()
    except sqlite3.OperationalError:  # Table doesn’t exist, version is 0
        version = 0

    # Apply all migrations starting from the DB’s version all the way up to the current version
    for i, migration in enumerate(migrations[version:]):
        if i == 0:
            path = pathlib.Path(db_file)
            name, ext = os.path.splitext(path.name)
            shutil.copy(db_file, path.parent / f'{name}-old_{constants.VERSION}{ext}')
        migration.migrate(connection)

    connection.close()
