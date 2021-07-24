import os
import re
import sqlite3
import typing as typ

import cv2
import skimage.metrics as sk_measure
import sympy as sp

from .dao import DAO
from .. import model
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
            return list(map(lambda r: model.Image(int(r[0]), r[1]), results))
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
        """Tells if the given image is already registered. Images are compared based on files names.

        :param image_path: Path to the image.
        :return: True if the image is registered; false otherwise. Returns None if an exception occured.
        """
        return self._test_image_registered_file_name(image_path)

    def _test_image_registered_file_name(self, image_path):
        # Only checks if another file in the same directory has the same name
        try:
            filename = re.escape(image_path)
            cursor = self._connection.execute('SELECT COUNT(*) FROM images WHERE path REGEXP ?', (filename,))
            return cursor.fetchall()[0][0] > 0
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    # TEST Experimental, use at your own risk.
    def _test_image_registered_pixels(self, image_path):
        # Uses OpenCV2 to compare pixels
        cursor = self._connection.execute('SELECT path FROM images')
        array1 = cv2.imread(image_path)
        size1 = len(array1), len(array1[0])

        for path, in cursor.fetchall():
            if os.path.exists(path):
                array2 = cv2.imread(path)
                size2 = len(array2), len(array2[0])
                if size1 == size2:
                    score = sk_measure.structural_similarity(
                        array1, array2,
                        multichannel=True,
                        gaussian_weights=True,
                        sigma=1.5,
                        use_sample_covariance=False
                    )
                    if score == 1:
                        return True

        return False

    def add_image(self, image_path: str, tags: typ.List[model.Tag]) -> bool:
        """Adds an image.

        :param image_path: Path to the image.
        :param tags: Image’s tags.
        :return: True if the image was added.
        """
        try:
            self._connection.execute('BEGIN')
            image_cursor = self._connection.cursor()
            image_cursor.execute('INSERT INTO images(path) VALUES(?)', (image_path,))
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
            s = str(sympy_expr)
            if ':' in s:
                metatag, value = s.split(':')
                if not ImageDao.check_metatag_value(metatag, value):
                    raise ValueError(_t('query_parser.error.invalid_metatag_value', value=value, metatag=metatag))
                return ImageDao._metatag_query(metatag, value)
            else:
                return f"""
                SELECT I.id, I.path
                FROM images AS I, tags AS T, image_tag AS IT
                WHERE T.label = "{s}"
                  AND T.id = IT.tag_id
                  AND IT.image_id = I.id
                """
        elif isinstance(sympy_expr, sp.Or):
            subs = [ImageDao._get_query(arg) for arg in sympy_expr.args]
            return 'SELECT id, path FROM (' + '\nUNION\n'.join(subs) + ')'
        elif isinstance(sympy_expr, sp.And):
            subs = [ImageDao._get_query(arg) for arg in sympy_expr.args]
            return 'SELECT id, path FROM (' + '\nINTERSECT\n'.join(subs) + ')'
        elif isinstance(sympy_expr, sp.Not):
            return f'SELECT id, path FROM (SELECT id, path FROM images EXCEPT ' \
                   f'{ImageDao._get_query(sympy_expr.args[0])})'
        elif sympy_expr == sp.true:
            return 'SELECT id, path FROM images'
        elif sympy_expr == sp.false:
            return None

        raise Exception(f'invalid symbol type “{type(sympy_expr)}”')

    @staticmethod
    def metatag_exists(metatag: str) -> bool:
        """Checks if the given metatag exists.

        :param metatag: The metatag to check.
        :return: True if the metatag exists.
        """
        return metatag in ImageDao._METATAGS

    @staticmethod
    def check_metatag_value(metatag: str, value: str) -> bool:
        """Checks the validity of a value for the given metatag.

        :param metatag: The metatag.
        :param value: Metatag’s value.
        :return: True if the value is valid.
        :exception: ValueError if the given metatag doesn’t exist.
        """
        if not ImageDao.metatag_exists(metatag):
            raise ValueError(_t('query_parser.error.unknown_metatag', metatag=metatag))
        return ImageDao._METATAGS[metatag][0](value)

    @staticmethod
    def _metatag_query(metatag: str, value: str) -> str:
        """Returns the SQL query for the given metatag.

        :param metatag: The metatag.
        :param value: Metatag’s value.
        :return: The SQL query for the metatag.
        """
        # Unescape space character, escape dot and replace '*' wildcard by a regex
        escaped_value = value.replace(r'\ ', ' ').replace('.', r'\.').replace('*', '[^/]*')
        return ImageDao._METATAGS[metatag][1].format(escaped_value)

    METAVALUE_PATTERN = r'(?:[\w.*-]|\\ )+'
    _METAVALUE_REGEX = re.compile(f'^{METAVALUE_PATTERN}$')

    # Declared metatags with their value-checking function and database query template.
    _METATAGS: typ.Dict[str, typ.Tuple[typ.Callable[[str], bool], str]] = {
        'ext': (lambda v: ImageDao._METAVALUE_REGEX.match(v) is not None,
                r'SELECT id, path FROM images WHERE path REGEXP "\.{}$"'),
        'name': (lambda v: ImageDao._METAVALUE_REGEX.match(v) is not None,  # TODO regex instead of simple *
                 r'SELECT id, path FROM images WHERE path REGEXP "/{}\.\w+$"'),
    }
