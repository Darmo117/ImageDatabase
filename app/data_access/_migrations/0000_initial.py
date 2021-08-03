"""Migrates from database from app version 3.1 to 3.2."""
import sqlite3

from app import utils, constants, data_access, gui
from app.i18n import translate as _t


def migrate(connection: sqlite3.Connection, thread: gui.threads.WorkerThread):
    connection.executescript(f"""
    BEGIN;
    CREATE TABLE version (
      db_version INTEGER PRIMARY KEY,
      app_version TEXT
    );
    ALTER TABLE images ADD COLUMN hash BLOB; -- Cannot use INTEGER as hashes are 64-bit *unsigned* integers
    CREATE INDEX idx_images_hash ON images (hash); -- Speed up hash querying
--     ALTER TABLE tags ADD COLUMN definition TEXT;
    INSERT INTO version (db_version, app_version) VALUES (1, "{constants.VERSION}");
    """)

    cursor = connection.execute('SELECT id, path FROM images')
    rows = cursor.fetchall()
    total_rows = len(rows)
    for i, (ident, path) in enumerate(rows):
        if thread.cancelled:
            cursor.close()
            connection.rollback()
            break

        thread.progress_signal.emit(
            i / total_rows,
            _t(f'popup.database_update.migration_0000.hashing_image_text', image=path, index=i + 1,
               total=total_rows),
            thread.STATUS_UNKNOWN
        )
        image_hash = utils.image.get_hash(path)
        try:
            connection.execute(
                'UPDATE images SET hash = ? WHERE id = ?',
                (data_access.ImageDao.encode_hash(image_hash) if image_hash is not None else None, ident)
            )
        except sqlite3.Error as e:
            thread.error = str(e)
            thread.cancel()
        thread.progress_signal.emit(
            (i + 1) / total_rows,
            _t(f'popup.database_update.migration_0000.hashing_image_text', image=path, index=i + 1,
               total=total_rows),
            thread.STATUS_SUCCESS
        )
    else:
        cursor.close()
        connection.commit()
