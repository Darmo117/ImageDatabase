import sqlite3
import typing as typ

import PyQt5.QtGui as QtGui

from ..logging import logger
from .dao import DAO
from .. import model


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

    NORMAL = 0
    COMPOUND = 1

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

    def get_all_tags(self, tag_class: typ.Optional[type] = None, sort_by_label=False, get_count=False) \
            -> typ.Optional[typ.List[typ.Union[typ.Tuple[model.Tag, int], model.Tag]]]:
        """
        Returns all tags. Result can be sorted by label. You can also query use count for each tag.

        :param tag_class: Sets type of tags to return. If None all tags wil be returned.
        :param sort_by_label: Result will be sorted by label using lexicographical ordering.
        :param get_count: If true, result will be a list of tuples containing the tag and its use count.
        :return: The list of tags or tag/count pairs or None if an exception occured.
        """
        try:
            query = "SELECT id, label, type_id, definition"
            if get_count:
                query += ", (SELECT COUNT(tag_id) FROM image_tag WHERE tags.id = tag_id) AS count"
            query += " FROM tags"
            if sort_by_label:
                query += " ORDER BY label"
            cursor = self._connection.execute(query)

            def row_to_tag(row: typ.Tuple[int, str, int, str, int]) \
                    -> typ.Optional[typ.Union[typ.Tuple[model.Tag, int], model.Tag]]:
                tag_type = model.TagType.from_id(row[2]) if row[2] is not None else None
                if row[3] is None and (tag_class == model.Tag or tag_class is None):
                    tag = model.Tag(row[0], row[1], tag_type)
                elif row[3] is not None and (tag_class == model.CompoundTag or tag_class is None):
                    tag = model.CompoundTag(row[0], row[1], row[3], tag_type)
                else:
                    return None
                return (tag, int(row[4])) if get_count else tag

            return list(filter(lambda t: t is not None, map(row_to_tag, cursor.fetchall())))
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    def tag_exists(self, tag_id: int, tag_name: str) -> typ.Optional[bool]:
        """
        Checks wether a tag with the same name exists.

        :param tag_id: Tag's ID.
        :param tag_name: Tag's name.
        :return: True if a tag with the same name already exists.
        """
        try:
            return self._connection.execute("SELECT COUNT(*) FROM tags WHERE label = ? AND id != ?",
                                            (tag_name, tag_id)).fetchall()[0][0] != 0
        except sqlite3.OperationalError as e:
            logger.exception(e)
            return None

    def get_tag_class(self, tag_name: str) -> typ.Union[typ.Type[model.Tag], typ.Type[model.CompoundTag], None]:
        """
        Returns the type of the given tag if any.

        :param tag_name: Tag's name.
        :return: Tag's class or None if tag doesn't exist.
        """
        try:
            cursor = self._connection.execute("SELECT definition FROM tags WHERE label = ?", (tag_name,))
            results = cursor.fetchall()
            if len(results) == 0:
                return None
            return model.Tag if results[0][0] is None else model.CompoundTag
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            logger.exception(e)
            return None

    def add_compound_tag(self, tag: model.CompoundTag) -> bool:
        """
        Adds a compound tag.

        :param tag: The compound tag to add.
        :return: True if the type was added or None if an exception occured.
        """
        try:
            self._connection.execute("INSERT INTO tags (label, type_id, definition) VALUES (?, ?, ?)",
                                     (tag.label, tag.type.id if tag.type is not None else None, tag.definition))
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
            logger.exception(e)
            return False

    def update_tag(self, tag: model.Tag) -> bool:
        """
        Updates the given tag.

        :param tag: The tag to update.
        :return: True if the tag was updated.
        """
        try:
            tag_type = tag.type.id if tag.type is not None else None
            if isinstance(tag, model.CompoundTag):
                self._connection.execute("UPDATE tags SET label = ?, type_id = ?, definition = ? WHERE id = ?",
                                         (tag.label, tag_type, tag.definition, tag.id))
            else:
                self._connection.execute("UPDATE tags SET label = ?, type_id = ? WHERE id = ?",
                                         (tag.label, tag_type, tag.id))
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
