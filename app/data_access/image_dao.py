import pathlib
import re
import sqlite3
import typing as typ

import sympy as sp

from .dao import DAO
from .tags_dao import TagsDao
from .. import model, utils
from ..i18n import translate as _t
from ..logging import logger


class ImageDao(DAO):
    """This class manages images."""

    def get_images(self, tags: sp.Basic) -> typ.Optional[typ.List[model.Image]]:
        """Returns all images matching the given tags.

        :param tags: Tags query.
        :return: All images matching the tags or None if an exception occured.
        """
        query = self._get_query(tags)
        if query is None:
            return []
        cursor = self._connection.cursor()
        try:
            cursor.execute(query)
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return None
        else:
            results = cursor.fetchall()
            cursor.close()
            return [self._get_image(r) for r in results]

    def get_tagless_images(self) -> typ.Optional[typ.List[model.Image]]:
        """Returns the list of images that do not have any tag.

        :return: The list of images or None if an error occured.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute("""
            SELECT I.id, I.path, I.hash
            FROM images AS I
            WHERE (
                SELECT COUNT(*)
                FROM image_tag
                WHERE image_id = I.id
            ) = 0
            """)
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return None
        else:
            results = cursor.fetchall()
            cursor.close()
            return [self._get_image(r) for r in results]

    def get_image_tags(self, image_id: int, tags_dao: TagsDao) -> typ.Optional[typ.List[model.Tag]]:
        """Returns all tags for the given image.

        :param image_id: Image’s ID.
        :param tags_dao: Tags DAO instance.
        :return: The tags for the image or None if an exception occured.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute("""
            SELECT T.id, T.label, T.type_id
            FROM tags AS T, image_tag AS IT
            WHERE IT.image_id = ?
              AND IT.tag_id = T.id
            """, (image_id,))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return None
        else:
            def row_to_tag(row: tuple) -> model.Tag:
                tag_type = tags_dao.get_tag_type_from_id(row[2]) if row[2] is not None else None
                return model.Tag(row[0], row[1], tag_type)

            tags = list(map(row_to_tag, cursor.fetchall()))
            cursor.close()
            return tags

    IMG_REGISTERED = 0
    """Indicates that the given image is already registered."""
    IMG_SIMILAR = 1
    """Indicates that the given image may already be registered."""
    IMG_NOT_REGISTERED = 2
    """Indicates that the given image is not registered."""

    def image_registered(self, image_path: pathlib.Path) -> typ.Optional[int]:
        """Tells whether other similar images may have already been registered.
        Two images are considered similar if the Hamming distance between their respective hashes is ≤ 10
        (cf. http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html) or if their
        paths are the exact same. Hashes are computed using the “difference hashing” method
        (cf. https://www.pyimagesearch.com/2017/11/27/image-hashing-opencv-python/).

        @see IMG_REGISTERED, IMG_SIMILAR, IMG_NOT_REGISTERED

        :param image_path: Path to the image.
        :return: An int corresponding to the registration state. Returns None if an error occured.
        """
        images = self.get_similar_images(image_path)
        if images is None:
            return None
        if any([e[3] for e in images]):
            return self.IMG_REGISTERED
        return self.IMG_SIMILAR if images else self.IMG_NOT_REGISTERED

    def get_similar_images(self, image_path: pathlib.Path) \
            -> typ.Optional[typ.List[typ.Tuple[model.Image, int, float, bool]]]:
        """Returns a list of all images that may be similar to the given one.

        :param image_path: Path to the image.
        :return: A list of candidate images with their Hamming distance, confidence score and a boolean indicating
            whether the paths are the same (True) or not (False).
        """
        image_hash = utils.image.get_hash(image_path)
        if image_hash is None:
            return None
        images = []
        for registered_image in self.get_images(sp.true):
            if image_path == registered_image.path:
                images.append((registered_image, 0, 1.0, True))
            elif registered_image.hash is not None \
                    and utils.image.compare_hashes(image_hash, registered_image.hash)[2]:
                images.append(
                    (registered_image, *utils.image.compare_hashes(image_hash, registered_image.hash)[:2], False))
        # Sort by: sameness (desc), distance (asc), confidence (desc), path (normal)
        return sorted(images, key=lambda e: (not e[3], e[1], -e[2], e[0]))

    def add_image(self, image_path: pathlib.Path, tags: typ.List[model.Tag]) -> bool:
        """Adds an image.

        :param image_path: Path to the image.
        :param tags: Image’s tags.
        :return: True if the image was added.
        """
        try:
            self._connection.execute('BEGIN')
            image_cursor = self._connection.cursor()
            image_hash = utils.image.get_hash(image_path) or 0
            image_cursor.execute(
                'INSERT INTO images(path, hash) VALUES(?, ?)',
                (str(image_path), self.encode_hash(image_hash) if image_hash is not None else None)
            )
            for tag in tags:
                tag_id = self._insert_tag_if_not_exists(tag)
                self._connection.execute('INSERT INTO image_tag(image_id, tag_id) VALUES(?, ?)',
                                         (image_cursor.lastrowid, tag_id))
        except sqlite3.Error as e:
            logger.exception(e)
            self._connection.rollback()
            return False
        else:
            self._connection.commit()
            return True

    def update_image(self, image_id: int, new_path: pathlib.Path, new_hash: typ.Union[int, None]) -> bool:
        """Sets the path of the given image.

        :param image_id: Image’s ID.
        :param new_path: The new path.
        :param new_hash: The new hash.
        :return: True if the image was updated.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute(
                'UPDATE images SET path = ?, hash = ? WHERE id = ?',
                (str(new_path), self.encode_hash(new_hash) if new_hash is not None else None, image_id)
            )
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return False
        else:
            cursor.close()
            return True

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
        except sqlite3.Error as e:
            logger.exception(e)
            self._connection.rollback()
            return False
        else:
            self._connection.commit()
            return True

    def delete_image(self, image_id: int) -> bool:
        """Deletes the given image.

        :param image_id: Image’s ID.
        :return: True if the image was deleted.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('DELETE FROM images WHERE id = ?', (image_id,))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return False
        else:
            cursor.close()
            return True

    def _get_image(self, result: typ.Tuple[int, str, bytes]) -> model.Image:
        """Creates an Image object from a result tuple."""
        return model.Image(
            id=result[0],
            path=pathlib.Path(result[1]).absolute(),
            hash=self.decode_hash(result[2]) if result[2] is not None else None
        )

    def _insert_tag_if_not_exists(self, tag: model.Tag) -> int:
        """Inserts the given tag if it does not already exist.

        :return: The tag’s ID.
        """
        cursor = self._connection.cursor()
        cursor.execute('SELECT id FROM tags WHERE label = ?', (tag.label,))
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
                value = value.replace(r'\(', '(').replace(r'\)', ')')
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
            if metatag == 'similar_to':
                return True
            return not re.search(r'((?<!\\)\\(?:\\\\)*)([^*?\\]|$)', value)
        else:
            if metatag == 'similar_to':
                return False
            try:
                re.compile(value)
            except re.error:
                return False
            return True

    @staticmethod
    def escape_metatag_plain_value(s: str) -> str:
        """Escapes all special characters of plain text mode."""
        return re.sub(r'([\\"*?])', r'\\\1', s)

    @staticmethod
    def _metatag_query(metatag: str, value: str, mode: str) -> str:
        """Returns the SQL query for the given metatag.

        :param metatag: The metatag.
        :param value: Metatag’s value.
        :return: The SQL query for the metatag.
        """
        if mode == 'plain':
            if metatag == 'similar_to':
                value = value.replace('\\', r'\\')
            else:
                # Escape regex meta-characters except * and ?
                value = re.sub(r'([\[\]()+{.^$])', r'\\\1', value)
                # Replace '*' and '?' by a regex
                value = re.sub(r'((?<!\\)(?:\\\\)*)([*?])', r'\1.\2', value)
                value = f'^{value}$'
        value = value.replace('"', '""')  # Escape "
        return ImageDao._METATAG_QUERIES[metatag].format(value)

    _METATAG_QUERIES = {
        'ext': """
        SELECT id, path, hash
        FROM images
        WHERE SUBSTR(path, RINSTR(path, ".") + 1) REGEXP "{0}"
        """,
        'name': """
        SELECT id, path, hash
        FROM images
        WHERE SUBSTR(path, RINSTR(path, "/") + 1) REGEXP "{0}"
        """,
        'path': """
        SELECT id, path, hash
        FROM images
        WHERE path REGEXP "{0}"
        """,
        'similar_to': """
        SELECT id, path, hash
        FROM images
        WHERE hash IS NOT NULL
          AND path != "{0}"
          AND SIMILAR(hash, (
            SELECT hash
            FROM images
            WHERE path = "{0}"
          ))
        """,
    }
