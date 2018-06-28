import sqlite3
import typing as typ

import PyQt5.QtGui as QtGui

import app.model as model
from app.logging import logger
from .dao import DAO


class TagsDao(DAO):
    """This class manages tags and tag types."""

    def get_all_types(self) -> typ.Optional[typ.List[model.TagType]]:
        """
        Returns all tag types.

        :return: All tag types or None if an exception occured.
        """
        try:
            cursor = self._connection.execute("SELECT id, label, symbol, color FROM tag_types")
            return [model.TagType(t[0], t[1], t[2], QtGui.QColor.fromRgb(t[3])) for t in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    def get_all_tags(self, sort_by_label=False, get_count=False) \
            -> typ.Optional[typ.List[typ.Union[typ.Tuple[model.Tag, int], model.Tag]]]:
        """
        Returns all tags. Result can be sorted by label. You can also query use count for each tag.

        :param sort_by_label: Result will be sorted by label using lexicographical ordering.
        :param get_count: If true, result will be a list of tuples containing the tag and its use count.
        :return: The list of tags or tag/count pairs or None if an exception occured.
        """
        try:
            query = "SELECT id, label, type_id"
            if get_count:
                query += ", (SELECT COUNT(tag_id) FROM image_tag WHERE tags.id = tag_id) AS count"
            query += " FROM tags"
            if sort_by_label:
                query += " ORDER BY label"
            cursor = self._connection.execute(query)

            def row_to_tag(row: tuple) -> typ.Union[typ.Tuple[model.Tag, int], model.Tag]:
                type = model.TagType.from_id(row[2]) if row[2] is not None else None
                tag = model.Tag(row[0], row[1], type)
                return (tag, int(row[3])) if get_count else tag

            return list(map(row_to_tag, cursor.fetchall()))
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    def add_type(self, tag_type: model.TagType) -> bool:
        """
        Adds a tag type.

        :param tag_type: The type to add.
        :return: True if the type was added or None if an exception occured.
        """
        try:
            self._connection.execute("INSERT INTO tag_types (label, symbol, color) VALUES (?, ?, ?)",
                                     (tag_type.label, tag_type.symbol, tag_type.color.rgb()))
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            logger.exception(e)
            return False

    def update_type(self, tag_type: model.TagType) -> bool:
        """
        Updates a tag type.

        :param tag_type: The tag type to update.
        :return: True if the type was updated.
        """
        try:
            self._connection.execute("UPDATE tag_types SET label = ?, symbol = ?, color = ? WHERE id = ?",
                                     (tag_type.label, tag_type.symbol, tag_type.color.rgb(), tag_type.id))
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            logger.exception(e)
            return False

    def delete_type(self, type_id: int) -> bool:
        """
        Deletes the given tag type.

        :param type_id: ID of the tag type to delete.
        :return: True if the type was deleted.
        """
        try:
            self._connection.execute("DELETE FROM tag_types WHERE id = ?", (type_id,))
            return True
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return False

    def update_tag(self, tag: model.Tag) -> bool:
        """
        Updates the given tag.

        :param tag: The tag to update.
        :return: True if the tag was updated.
        """
        try:
            type = tag.type.id if tag.type is not None else None
            self._connection.execute("UPDATE tags SET label = ?, type_id = ? WHERE id = ?", (tag.label, type, tag.id))
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            logger.exception(e)
            return False

    def delete_tag(self, tag_id: int) -> bool:
        """
        Deletes the given tag.

        :param tag_id: ID of the tag to delete.
        :return: True if the tag was deleted.
        """
        try:
            self._connection.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            return True
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return False
