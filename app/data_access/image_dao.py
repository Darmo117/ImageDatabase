import re
import sqlite3
import typing as typ

import sympy as sp

from .dao import DAO
from .. import model, utils
from ..i18n import translate as _t
from ..logging import logger


class ImageDao(DAO):
    """This class manages images."""

    def get_images(self, tags: sp.Basic) -> typ.Optional[typ.List[model.Image]]:
        """Returns all images matching the given tags.

        :param tags: List of tags.
        :return: All images matching the tags or None if an exception occured.
        """
        try:
            query = self._get_query(tags)
            if query is None:
                return []
            results = self._connection.execute(query).fetchall()
            return [model.Image(id=r[0], path=r[1], hash=r[2]) for r in results]
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    def get_image_tags(self, image_id: int) -> typ.Optional[typ.List[model.Tag]]:
        """Returns all tags for the given image.

        :param image_id: Image’s ID.
        :return: The tags for the image or None if an exception occured.
        """
        try:
            cursor = self._connection.execute("""
            SELECT T.id, T.label, T.type_id
            FROM tags AS T, image_tag AS IT
            WHERE IT.image_id = ?
              AND IT.tag_id = T.id
            """, (image_id,))

            def row_to_tag(row: tuple) -> model.Tag:
                tag_type = model.TagType.from_id(row[2]) if row[2] is not None else None
                return model.Tag(row[0], row[1], tag_type)

            return list(map(row_to_tag, cursor.fetchall()))
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    def image_registered(self, image_path: str) -> typ.Optional[bool]:
        """Tells whether other similar images may have already been registered.
        Two images are considered similar if the Hamming distance between their respective hashes is ≤ 10
        (cf. http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html) or if their
        paths are the exact same. Hashes are computed using the “difference hashing” method
        (cf. https://www.pyimagesearch.com/2017/11/27/image-hashing-opencv-python/).

        :param image_path: Path to the image.
        :return: True if similar images were found; false otherwise. Returns None if an error occured.
        """
        image_hash = utils.image.get_hash(image_path)
        if image_hash is None:
            return None
        return any([image_hash == registered_image.path
                    or (registered_image.hash is not None
                        and utils.image.compare_hashes(image_hash, registered_image.hash)[2])
                    for registered_image in self.get_images(sp.true)])

    def add_image(self, image_path: str, tags: typ.List[model.Tag]) -> bool:
        """Adds an image.

        :param image_path: Path to the image.
        :param tags: Image’s tags.
        :return: True if the image was added.
        """
        try:
            self._connection.execute('BEGIN')
            image_cursor = self._connection.cursor()
            image_hash = utils.image.get_hash(image_path) or 0
            image_cursor.execute('INSERT INTO images(path, hash) VALUES(?, ?)', (image_path, image_hash))
            for tag in tags:
                tag_id = self._insert_tag_if_not_exists(tag)
                self._connection.execute('INSERT INTO image_tag(image_id, tag_id) VALUES(?, ?)',
                                         (image_cursor.lastrowid, tag_id))
            self._connection.commit()
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            self._connection.rollback()
            logger.exception(e)
            return False

    def update_image_path(self, image_id: int, new_path: str) -> bool:
        """Sets the path of the given image.

        :param image_id: Image’s ID.
        :param new_path: The new path.
        :return: True if the image was updated.
        """
        try:
            self._connection.execute('UPDATE images SET path = ? WHERE id = ?', (new_path, image_id))
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            self._connection.rollback()
            logger.exception(e)
            return False

    def update_image_tags(self, image_id: int, tags: typ.List[model.Tag]) -> bool:
        """Sets the tags for the given image.

        :param image_id: Image’s ID.
        :param tags: The tags to set.
        :return: True if the image was added.
        """
        try:
            self._connection.execute('BEGIN')
            self._connection.execute('DELETE FROM image_tag WHERE image_id = ?', (image_id,))
            for tag in tags:
                tag_id = self._insert_tag_if_not_exists(tag)
                self._connection.execute('INSERT INTO image_tag(image_id, tag_id) VALUES(?, ?)', (image_id, tag_id))
            self._connection.commit()
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            self._connection.rollback()
            logger.exception(e)
            return False

    def delete_image(self, image_id: int) -> bool:
        """Deletes the given image.

        :param image_id: Image’s ID.
        :return: True if the image was deleted.
        """
        try:
            self._connection.execute('DELETE FROM images WHERE id = ?', (image_id,))
            return True
        except sqlite3.OperationalError as e:
            self._connection.rollback()
            logger.exception(e)
            return False

    def _insert_tag_if_not_exists(self, tag: model.Tag) -> int:
        """Inserts the given tag if it does not already exist.

        :return: The tag’s ID.
        """
        cursor = self._connection.execute('SELECT id FROM tags WHERE label = ?', (tag.label,))
        result = cursor.fetchone()
        cursor.close()
        if result is None:
            cursor = self._connection.cursor()
            tag_type = tag.type.id if tag.type is not None else None
            cursor.execute('INSERT INTO tags(label, type_id) VALUES(?, ?)', (tag.label, tag_type))
            return cursor.lastrowid
        return result[0]

    @staticmethod
    def _get_query(sympy_expr: sp.Basic) -> typ.Optional[str]:
        """Transforms a SymPy expression into an SQL query.

        :param sympy_expr: The SymPy query.
        :return: The SQL query or None if the argument is a contradiction.
        """
        if isinstance(sympy_expr, sp.Symbol):
            tag_name = sympy_expr.name
            if ':' in tag_name:
                metatag, mode, value = tag_name.split(':', maxsplit=2)
                if not ImageDao.check_metatag_value(metatag, value, mode):
                    raise ValueError(_t('query_parser.error.invalid_metatag_value', value=value, metatag=metatag))
                return ImageDao._metatag_query(metatag, value, mode)
            else:
                return f"""
                SELECT I.id, I.path, I.hash
                FROM images AS I, tags AS T, image_tag AS IT
                WHERE T.label = "{tag_name}"
                  AND T.id = IT.tag_id
                  AND IT.image_id = I.id
                """
        elif isinstance(sympy_expr, sp.Or):
            subs = [ImageDao._get_query(arg) for arg in sympy_expr.args if arg]
            return 'SELECT id, path, hash FROM (' + '\nUNION\n'.join(subs) + ')'
        elif isinstance(sympy_expr, sp.And):
            subs = [ImageDao._get_query(arg) for arg in sympy_expr.args if arg]
            return 'SELECT id, path, hash FROM (' + '\nINTERSECT\n'.join(subs) + ')'
        elif isinstance(sympy_expr, sp.Not):
            sub = ImageDao._get_query(sympy_expr.args[0])
            return f'SELECT id, path, hash FROM images' + (f' EXCEPT {sub}' if sub else '')
        elif sympy_expr == sp.true:
            return 'SELECT id, path, hash FROM images'
        elif sympy_expr == sp.false:
            return None

        raise Exception(f'invalid symbol type “{type(sympy_expr)}”')

    @staticmethod
    def metatag_exists(metatag: str) -> bool:
        """Checks if the given metatag exists.

        :param metatag: The metatag to check.
        :return: True if the metatag exists.
        """
        return metatag in ImageDao._METATAG_QUERIES

    @staticmethod
    def check_metatag_value(metatag: str, value: str, mode: str) -> bool:
        """Checks the validity of a value for the given metatag.

        :param metatag: The metatag.
        :param value: Metatag’s value.
        :param mode: 'plain' for plain text or 'regex' for regex.
        :return: True if the value is valid.
        :exception: ValueError if the given metatag doesn’t exist.
        """
        if not ImageDao.metatag_exists(metatag):
            raise ValueError(_t('query_parser.error.unknown_metatag', metatag=metatag))
        if mode == 'plain':
            return not re.search(r'((?<!\\)\\(?:\\\\)*)([^*?\\]|$)', value)
        else:
            try:
                re.compile(value)
            except re.error:
                return False
            return True

    @staticmethod
    def _metatag_query(metatag: str, value: str, mode: str) -> str:
        """Returns the SQL query for the given metatag.

        :param metatag: The metatag.
        :param value: Metatag’s value.
        :return: The SQL query for the metatag.
        """
        if mode == 'plain':
            # Escape regex meta-characters except * and ?
            value = re.sub(r'([\[\]()+{.^$])', r'\\\1', value)
            # Replace '*' and '?' by a regex
            value = re.sub(r'((?<!\\)(?:\\\\)*)([*?])', r'\1[^/]\2', value)
            value = f'^{value}$'
        value = value.replace('"', '""')  # Escape "
        return ImageDao._METATAG_QUERIES[metatag].format(value)

    _METATAG_QUERIES = {
        'ext': r'SELECT id, path, hash FROM images WHERE SUBSTR(path, RINSTR(path, ".") + 1) REGEXP "{}"',
        'name': r'SELECT id, path, hash FROM images WHERE SUBSTR(path, RINSTR(path, "/") + 1) REGEXP "{}"',
        # TODO similar:<image name> -> returns all images that are similar, no joker or regex
    }
