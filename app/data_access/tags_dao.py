import sqlite3
import typing as typ

import PyQt5.QtGui as QtG

from .dao import DAO
from .. import model
from ..logging import logger

_T = typ.TypeVar('_T', model.Tag, model.CompoundTag)


class TagsDao(DAO):
    """This class manages tags and tag types."""

    def get_all_types(self) -> typ.Optional[typ.List[model.TagType]]:
        """Returns all tag types.

        :return: All tag types or None if an exception occured.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('SELECT id, label, symbol, color FROM tag_types')
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return None
        else:
            types = [self._get_tag_type(t) for t in cursor.fetchall()]
            cursor.close()
            return types

    def is_special_char(self, c: str) -> bool:
        """Tells if a character is a type symbol.

        :param c: The character to check.
        :return: True if the argument is a type symbol.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('SELECT * FROM tag_types WHERE symbol = ?', (c,))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return False
        else:
            special = len(cursor.fetchall()) != 0
            cursor.close()
            return special

    def create_tag_from_string(self, s: str) -> model.Tag:
        """Creates a new Tag instance from a given string.

        :param s: The string to parse.
        :return: The corresponding tag.
        """
        has_type = self.is_special_char(s[0])
        label = s[1:] if has_type else s
        tag_type = self.get_tag_type_from_symbol(s[0]) if has_type else None
        return model.Tag(0, label, tag_type)

    def get_tag_type_from_symbol(self, symbol: str) -> typ.Optional[model.TagType]:
        """Returns the type with from the given symbol.

        :param symbol: The type symbol.
        :return: The corresponding type.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('SELECT id, label, symbol, color FROM tag_types WHERE symbol = ?', (symbol,))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return None
        else:
            results = cursor.fetchall()
            cursor.close()
            if results:
                return self._get_tag_type(results[0])
            return None

    def get_tag_type_from_id(self, ident: int) -> typ.Optional[model.TagType]:
        """Returns the type with the given ID.

        :param ident: The SQLite ID.
        :return: The corresponding type.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('SELECT id, label, symbol, color FROM tag_types WHERE id = ?', (ident,))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return None
        else:
            results = cursor.fetchall()
            cursor.close()
            if results:
                return self._get_tag_type(results[0])
            return None

    def add_type(self, tag_type: model.TagType) -> bool:
        """Adds a tag type.

        :param tag_type: The type to add.
        :return: True if the type was added or None if an exception occured.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('INSERT INTO tag_types (label, symbol, color) VALUES (?, ?, ?)',
                           (tag_type.label, tag_type.symbol, tag_type.color.rgb()))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return False
        else:
            cursor.close()
            return True

    def update_type(self, tag_type: model.TagType) -> bool:
        """Updates a tag type.

        :param tag_type: The tag type to update.
        :return: True if the type was updated.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('UPDATE tag_types SET label = ?, symbol = ?, color = ? WHERE id = ?',
                           (tag_type.label, tag_type.symbol, tag_type.color.rgb(), tag_type.id))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return False
        else:
            cursor.close()
            return True

    def delete_type(self, type_id: int) -> bool:
        """Deletes the given tag type.

        :param type_id: ID of the tag type to delete.
        :return: True if the type was deleted.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('DELETE FROM tag_types WHERE id = ?', (type_id,))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return False
        else:
            cursor.close()
            return True

    def get_all_tags(self, tag_class: typ.Type[_T] = None, sort_by_label: bool = False, get_count: bool = False) \
            -> typ.Optional[typ.Union[typ.List[typ.Tuple[_T, int]], typ.List[_T]]]:
        """Returns all tags. Result can be sorted by label. You can also query use count for each tag.

        :param tag_class: Sets type of tags to return. If None all tags wil be returned.
        :param sort_by_label: Result will be sorted by label using lexicographical ordering.
        :param get_count: If true, result will be a list of tuples containing the tag and its use count.
        :return: The list of tags or tag/count pairs or None if an exception occured.
        """
        query = 'SELECT id, label, type_id, definition'
        if get_count:
            query += ', (SELECT COUNT(tag_id) FROM image_tag WHERE tags.id = tag_id) AS count'
        query += ' FROM tags'
        if sort_by_label:
            query += ' ORDER BY label'
        cursor = self._connection.cursor()
        try:
            cursor.execute(query)
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return None
        else:
            def row_to_tag(row: typ.Tuple[int, str, int, str, int]) \
                    -> typ.Optional[typ.Union[typ.Tuple[model.Tag, int], model.Tag]]:
                tag_type = self.get_tag_type_from_id(row[2]) if row[2] is not None else None
                if row[3] is None and (tag_class == model.Tag or tag_class is None):
                    tag = model.Tag(row[0], row[1], tag_type)
                elif row[3] is not None and (tag_class == model.CompoundTag or tag_class is None):
                    tag = model.CompoundTag(row[0], row[1], row[3], tag_type)
                else:
                    return None
                return (tag, int(row[4])) if get_count else tag

            tags = list(filter(lambda t: t is not None, map(row_to_tag, cursor.fetchall())))
            cursor.close()
            return tags

    def get_all_tag_types(self, sort_by_symbol: bool = False, get_count: bool = False) \
            -> typ.Optional[typ.Union[typ.List[model.TagType], typ.List[typ.Tuple[model.TagType, int]]]]:
        """Returns all tag types.

        :param sort_by_symbol: Whether to sort types by symbol along with labels.
        :param get_count: If true, result will be a list of tuples containing the tag type and its use count.
        :return: All currently defined tag types.
        """
        query = 'SELECT id, label, symbol, color'
        if get_count:
            query += ', (SELECT COUNT(*) FROM tags WHERE tag_types.id = type_id) AS count'
        query += ' FROM tag_types ORDER BY label'
        if sort_by_symbol:
            query += ', symbol'
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
            types = []
            for ident, label, symbol, color, *count in results:
                tag_type = self._get_tag_type((ident, label, symbol, color))
                types.append(tag_type if not get_count else (tag_type, count[0]))
            return types

    def tag_exists(self, tag_id: int, tag_name: str) -> typ.Optional[bool]:
        """Checks wether a tag with the same name exists.

        :param tag_id: Tag’s ID.
        :param tag_name: Tag’s name.
        :return: True if a tag with the same name already exists.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('SELECT COUNT(*) FROM tags WHERE label = ? AND id != ?', (tag_name, tag_id))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return None
        else:
            exists = cursor.fetchall()[0][0] != 0
            cursor.close()
            return exists

    def get_tag_class(self, tag_name: str) -> typ.Union[typ.Type[model.Tag], typ.Type[model.CompoundTag], None]:
        """Returns the type of the given tag if any.

        :param tag_name: Tag’s name.
        :return: Tag’s class or None if tag doesn't exist.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('SELECT definition FROM tags WHERE label = ?', (tag_name,))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return None
        else:
            results = cursor.fetchall()
            cursor.close()
            if len(results) == 0:
                return None
            return model.Tag if results[0][0] is None else model.CompoundTag

    def add_compound_tag(self, tag: model.CompoundTag) -> bool:
        """Adds a compound tag.

        :param tag: The compound tag to add.
        :return: True if the type was added or None if an exception occured.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('INSERT INTO tags (label, type_id, definition) VALUES (?, ?, ?)',
                           (tag.label, tag.type.id if tag.type is not None else None, tag.definition))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return False
        else:
            cursor.close()
            return True

    def update_tag(self, tag: model.Tag) -> bool:
        """Updates the given tag.

        :param tag: The tag to update.
        :return: True if the tag was updated.
        """
        tag_type = tag.type.id if tag.type is not None else None
        cursor = self._connection.cursor()
        try:
            if isinstance(tag, model.CompoundTag):
                cursor.execute('UPDATE tags SET label = ?, type_id = ?, definition = ? WHERE id = ?',
                               (tag.label, tag_type, tag.definition, tag.id))
            else:
                cursor.execute('UPDATE tags SET label = ?, type_id = ? WHERE id = ?',
                               (tag.label, tag_type, tag.id))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return False
        else:
            cursor.close()
            return True

    def delete_tag(self, tag_id: int) -> bool:
        """Deletes the given tag.

        :param tag_id: ID of the tag to delete.
        :return: True if the tag was deleted.
        """
        cursor = self._connection.cursor()
        try:
            cursor.execute('DELETE FROM tags WHERE id = ?', (tag_id,))
        except sqlite3.Error as e:
            logger.exception(e)
            cursor.close()
            return False
        else:
            cursor.close()
            return True

    @staticmethod
    def _get_tag_type(result: typ.Tuple[int, str, str, int]) -> model.TagType:
        """Creates an TagType object based on the given result tuple."""
        return model.TagType(
            ident=result[0],
            label=result[1],
            symbol=result[2],
            color=QtG.QColor.fromRgb(result[3])
        )
