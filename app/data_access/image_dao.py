import os
import re
import sqlite3

from sympy import Not, And, Or, Symbol, true, false

from app.logging import logger
from app.model import Image, Tag, TagType
from .dao import DAO


class ImageDao(DAO):
    def get_images(self, tags) -> list or None:
        try:
            query = ImageDao._get_query(tags)
            if query is None:
                return []
            results = self._connection.execute(query).fetchall()
            return list(map(lambda r: Image(int(r[0]), r[1]), results))
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    def get_image_tags(self, image_id) -> list or None:
        try:
            cursor = self._connection.execute("""
            SELECT T.id, T.label, T.type_id
            FROM tags AS T, image_tag as IT
            WHERE IT.image_id = ?
              AND IT.tag_id = T.id
            """, (image_id,))

            def f(t):
                type = TagType.from_id(t[2]) if t[2] is not None else None
                return Tag(t[0], t[1], type)

            return list(map(f, cursor.fetchall()))
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    def image_registered(self, image_path) -> bool or None:
        try:
            filename = re.escape("/" + os.path.basename(image_path))
            cursor = self._connection.execute("SELECT COUNT(*) FROM images WHERE path regexp ?", (filename,))
            return cursor.fetchall()[0][0] > 0
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    def add_image(self, image_path, tags) -> bool:
        try:
            self._connection.execute("BEGIN")
            image_cursor = self._connection.cursor()
            image_cursor.execute("INSERT INTO images(path) VALUES(?)", (image_path,))
            for tag in tags:
                tag_id = self._insert_tag_if_not_exists(tag)
                self._connection.execute("INSERT INTO image_tag(image_id, tag_id) VALUES(?, ?)",
                                         (image_cursor.lastrowid, tag_id))
            self._connection.commit()
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            self._connection.rollback()
            logger.exception(e)
            return False

    def update_image_path(self, image_id, new_path) -> bool:
        try:
            self._connection.execute("UPDATE images SET path = ? WHERE id = ?", (new_path, image_id))
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            self._connection.rollback()
            logger.exception(e)
            return False

    def update_image_tags(self, image_id, tags) -> bool:
        try:
            self._connection.execute("BEGIN")
            self._connection.execute("DELETE FROM image_tag WHERE image_id = ?", (image_id,))
            for tag in tags:
                tag_id = self._insert_tag_if_not_exists(tag)
                self._connection.execute("INSERT INTO image_tag(image_id, tag_id) VALUES(?, ?)", (image_id, tag_id))
            self._connection.commit()
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            self._connection.rollback()
            logger.exception(e)
            return False

    def delete_image(self, image_id) -> bool:
        try:
            self._connection.execute("DELETE FROM images WHERE id = ?", (image_id,))
            return True
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return False

    def _insert_tag_if_not_exists(self, tag: Tag) -> int:
        """:return: tag's ID"""
        cursor = self._connection.execute("SELECT id FROM tags WHERE label = ?", (tag.label,))
        result = cursor.fetchone()
        cursor.close()
        if result is None:
            cursor = self._connection.cursor()
            type = tag.type.id if tag.type is not None else None
            cursor.execute("INSERT INTO tags(label, type_id) VALUES(?, ?)", (tag.label, type))
            return cursor.lastrowid
        return result[0]

    @staticmethod
    def _get_query(sympy_expr) -> str or None:
        if isinstance(sympy_expr, Symbol):
            s = str(sympy_expr)
            if ":" in s:
                metatag, value = s.split(":")
                if not ImageDao.check_metatag_value(metatag, value):
                    raise ValueError("Invalid value '{}' for metatag '{}'!".format(value, metatag))
                return ImageDao._metatag_query(metatag, value)
            else:
                return """
                SELECT I.id, I.path
                FROM images AS I, tags AS T, image_tag AS IT
                WHERE T.label = "{}"
                  AND T.id = IT.tag_id
                  AND IT.image_id = I.id
                """.format(s)
        elif isinstance(sympy_expr, Or):
            subs = [ImageDao._get_query(arg) for arg in sympy_expr.args]
            return "SELECT id, path FROM (" + "\nUNION\n".join(subs) + ")"
        elif isinstance(sympy_expr, And):
            subs = [ImageDao._get_query(arg) for arg in sympy_expr.args]
            return "SELECT id, path FROM (" + "\nINTERSECT\n".join(subs) + ")"
        elif isinstance(sympy_expr, Not):
            return "SELECT id, path FROM images EXCEPT\n" + ImageDao._get_query(sympy_expr.args[0])
        elif sympy_expr == true:
            return "SELECT id, path FROM images"
        elif sympy_expr == false:
            return None

        raise Exception("Invalid symbol type '{}'!".format(str(type(sympy_expr))))

    @staticmethod
    def metatag_exists(metatag):
        return metatag in ImageDao._METATAGS

    @staticmethod
    def check_metatag_value(metatag, value):
        if not ImageDao.metatag_exists(metatag):
            raise ValueError("Unknown metatag '{}'!".format(metatag))
        return ImageDao._METATAGS[metatag][0](value)

    @staticmethod
    def _metatag_query(metatag, value):
        return ImageDao._METATAGS[metatag][1].format(value.replace("*", "[^/]*"))

    _METAVALUE_PATTERN = re.compile("^[\w.*-]+$")

    # Declared metatags with their value-checking function and database query.
    _METATAGS = {
        "type": (lambda v: ImageDao._METAVALUE_PATTERN.match(v),
                 "SELECT id, path FROM images WHERE path regexp '\.{}$'"),
        "name": (lambda v: ImageDao._METAVALUE_PATTERN.match(v),
                 "SELECT id, path FROM images WHERE path regexp '/{}\.\w+$'"),
    }


if __name__ == '__main__':
    dao = ImageDao()
    dao.add_image("test.jpg", ["a", "b"])
