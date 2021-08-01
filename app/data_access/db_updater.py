import os
import shutil
import sqlite3

from ._migrations import migrations
from .. import config, constants


def update_database_if_needed():
    """Updates the database if it needs to be."""
    db_file = config.CONFIG.database_path
    setup = not db_file.exists()
    connection = sqlite3.connect(str(db_file))
    connection.isolation_level = None

    if setup:
        with constants.DB_SETUP_FILE.open(encoding='UTF-8') as f:
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
        if i == 0 and not setup:
            name, ext = os.path.splitext(db_file.name)
            shutil.copy(db_file, db_file.parent / f'{name}-old_{app_version}{ext}')
        migration.migrate(connection)

    connection.close()
