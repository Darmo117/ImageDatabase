import sqlite3
from PyQt5.QtGui import QColor
from app.model import Tag, TagType
from .dao import DAO


class TagsDao(DAO):
    def get_all_types(self) -> list or None:
        try:
            cursor = self._connection.execute("SELECT id, label, symbol, color FROM tag_types")
            return [TagType(t[0], t[1], t[2], QColor.fromRgb(t[3])) for t in cursor.fetchall()]
        except sqlite3.OperationalError:
            return None

    def get_all_tags(self, sort_by_label=False, get_count=False) -> list or None:
        try:
            query = "SELECT id, label, type_id"
            if get_count:
                query += ", (SELECT COUNT(tag_id) FROM image_tag WHERE tags.id = tag_id) AS count"
            query += " FROM tags"
            if sort_by_label:
                query += " ORDER BY label"
            cursor = self._connection.execute(query)

            def f(t):
                type = TagType.from_id(t[2]) if t[2] is not None else None
                tag = Tag(t[0], t[1], type)
                return (tag, int(t[3])) if get_count else tag

            return list(map(f, cursor.fetchall()))
        except sqlite3.OperationalError:
            return None

    def add_type(self, tag_type: TagType) -> bool:
        try:
            self._connection.execute("INSERT INTO tag_types (label, symbol, color) VALUES (?, ?, ?)",
                                     (tag_type.label, tag_type.symbol, tag_type.color.rgb()))
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            return False

    def update_type(self, tag_type: TagType) -> bool:
        try:
            self._connection.execute("UPDATE tag_types SET label = ?, symbol = ?, color = ? WHERE id = ?",
                                     (tag_type.label, tag_type.symbol, tag_type.color.rgb(), tag_type.id))
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            return False

    def delete_type(self, type_id) -> bool:
        try:
            self._connection.execute("DELETE FROM tag_types WHERE id = ?", (type_id,))
            return True
        except sqlite3.OperationalError:
            return False

    def update_tag(self, tag: Tag) -> bool:
        try:
            type = tag.type.id if tag.type is not None else None
            self._connection.execute("UPDATE tags SET label = ?, type_id = ? WHERE id = ?", (tag.label, type, tag.id))
            return True
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            return False

    def delete_tag(self, tag_id) -> bool:
        try:
            self._connection.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            return True
        except sqlite3.OperationalError:
            return False
