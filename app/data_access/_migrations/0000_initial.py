"""Migrates from database from app version 3.1 to 3.2."""
import sqlite3

from ... import utils, constants


def migrate(connection: sqlite3.Connection):
    connection.executescript(f"""
    BEGIN;
    CREATE TABLE version (
      db_version INTEGER PRIMARY KEY,
      app_version TEXT
    );
    ALTER TABLE images ADD COLUMN hash BLOB; -- Cannot use INTEGER as hashes are 64-bit *unsigned* integers
    CREATE INDEX idx_images_hash ON images (hash); -- Speed up hash querying
    ALTER TABLE tags ADD COLUMN definition TEXT;
    INSERT INTO version (db_version, app_version) VALUES (1, "{constants.VERSION}");
    """)

    cursor = connection.execute('SELECT id, path FROM images')
    for entry in cursor.fetchall():
        ident, path = entry
        image_hash = utils.image.get_hash(path)
        connection.execute('UPDATE images SET hash = ? WHERE id = ?', (image_hash, ident))
    cursor.close()

    connection.commit()
