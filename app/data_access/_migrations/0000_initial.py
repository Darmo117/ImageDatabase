"""Migrates from database from app version 3.1 to 3.2."""
import sqlite3

import cv2

from ... import utils


def migrate(connection: sqlite3.Connection):
    connection.executescript("""
    CREATE TABLE db_version (
      version INTEGER PRIMARY KEY
    );
    ALTER TABLE images ADD COLUMN hash INTEGER;
    ALTER TABLE tags ADD COLUMN definition TEXT;
    BEGIN;
    INSERT INTO db_version (version) VALUES (1);
    """)

    cursor = connection.execute('SELECT id, path FROM images')
    for entry in cursor.fetchall():
        ident, path = entry
        image = cv2.imread(path)
        image_hash = utils.image.difference_hash(image) if image is not None else None
        connection.execute('UPDATE images SET hash = ? WHERE id = ?', (image_hash, ident))
    cursor.close()

    connection.commit()
