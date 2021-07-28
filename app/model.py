from __future__ import annotations

import re
import typing as typ
from dataclasses import dataclass

import PyQt5.QtGui as QtG


@dataclass(frozen=True, eq=True)
class Image:
    """This class represents an image."""
    id: int
    path: str
    hash: int

    def __lt__(self, other):
        if not isinstance(other, Image):
            raise ValueError(f'expected Image, got {type(other)}')
        return self.path < other.path

    def __gt__(self, other):
        if not isinstance(other, Image):
            raise ValueError(f'expected Image, got {type(other)}')
        return self.path > other.path

    def __le__(self, other):
        return self == other or self < other

    def __ge__(self, other):
        return self == other or self > other


class TagType:
    """This class represents a tag type."""
    LABEL_PATTERN = re.compile(r'^\S.*$')
    SYMBOL_PATTERN = re.compile(r'^[^\w+()\\:-]$')
    SYMBOL_TYPES = {}
    ID_TYPES = {}

    def __init__(self, ident: int, label: str, symbol: str, color: QtG.QColor = QtG.QColor(0, 0, 0)):
        """Creates a tag type.

        :param ident: Type’s SQLite ID.
        :param label: Type’s label.
        :param symbol: Type’s symbol.
        :param color: Type’s color.
        """
        if not self.LABEL_PATTERN.match(label):
            raise ValueError(f'illegal type label "{label}"')
        if not self.SYMBOL_PATTERN.match(symbol):
            raise ValueError(f'illegal type symbol "{symbol}"')
        self._id = ident
        self._label = label
        self._symbol = symbol
        self._color = color

    @property
    def id(self) -> int:
        """Returns this type’s ID."""
        return self._id

    @property
    def label(self) -> str:
        """Returns this type’s label."""
        return self._label

    @property
    def symbol(self) -> str:
        """Returns this type’s symbol."""
        return self._symbol

    @property
    def color(self) -> QtG.QColor:
        """Returns this type’s color."""
        return self._color

    def __eq__(self, other):
        if not isinstance(other, TagType):
            return False
        return (self.id == other.id and self.label == other.label and self.symbol == other.symbol and
                self._color == other.color)

    def __repr__(self):
        return f'TagType{{id={self.id}, label={self.label}, symbol={self.symbol}, color={self.color.name()}}}'

    @staticmethod
    def init(types: typ.Iterable[TagType]):
        """Initializes all available tag types.

        :param types: The available types.
        """
        TagType.SYMBOL_TYPES.clear()
        TagType.ID_TYPES.clear()
        for tag_type in types:
            TagType.SYMBOL_TYPES[tag_type.symbol] = tag_type
            TagType.ID_TYPES[tag_type.id] = tag_type

    @staticmethod
    def is_special_char(c: str) -> bool:
        """Tells if a character is a type symbol.

        :param c: The character to check.
        :return: True if the argument is a type symbol.
        """
        return c in TagType.SYMBOL_TYPES

    @staticmethod
    def from_symbol(symbol: str) -> TagType:
        """Returns the type with from the given symbol.

        :param symbol: The type symbol.
        :return: The corresponding type.
        """
        return TagType.SYMBOL_TYPES[symbol]

    @staticmethod
    def from_id(ident: int) -> TagType:
        """Returns the type with the given ID.

        :param ident: The SQLite ID.
        :return: The corresponding type.
        """
        return TagType.ID_TYPES[ident]


class Tag:
    """This class represents an image tag. Tags can be associated to a type."""
    LABEL_PATTERN = re.compile(r'^\w+$')

    def __init__(self, ident: int, label: str, tag_type: typ.Optional[TagType] = None):
        """Creates a tag with an optional type.

        :param ident: Tag’s SQLite ID.
        :param label: Tag’s label.
        :param tag_type: Tag’s type?
        """
        if not self.LABEL_PATTERN.match(label):
            raise ValueError(f'illegal tag label "{label}"')

        self._id = ident
        self._label = label
        self._type = tag_type

    def raw_label(self) -> str:
        """Returns the raw label, i.e. the name prefixed with its type symbol."""
        symbol = self._type.symbol if self._type is not None else ''
        return symbol + self._label

    @property
    def id(self) -> int:
        """Returns this tag’s SQLite ID."""
        return self._id

    @property
    def label(self) -> str:
        """Return this tag’s label."""
        return self._label

    @property
    def type(self) -> TagType:
        """Returns this tag’s type."""
        return self._type

    def __repr__(self):
        return self._label

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False
        return self.id == other.id and self.label == other.label and self.type == other.type

    @classmethod
    def from_string(cls, s: str) -> Tag:
        """Returns a tag instance from a given string.

        :param s: The string to parse.
        :return: The corresponding tag.
        :rtype: Tag
        """
        has_type = TagType.is_special_char(s[0])
        label = s[1:] if has_type else s
        tag_type = TagType.from_symbol(s[0]) if has_type else None
        return cls(0, label, tag_type)


class CompoundTag(Tag):
    """A compound tag is a tag defined by a tag query. This type of tags is only used in queries, they cannot be used to
    tag images directly.
    """

    def __init__(self, ident: int, label: str, definition: str, tag_type: typ.Optional[TagType] = None):
        """Creates a compound tag.

        :param ident: Tag’s SQLite ID.
        :param label: Tag’s label.
        :param definition: Tag’s definition (tag expression).
        :param tag_type: Tag’s optional type.
        """
        super().__init__(ident, label, tag_type=tag_type)
        self._definition = definition

    @property
    def definition(self) -> str:
        """Returns the tag expression defining this tag."""
        return self._definition

    def __eq__(self, other):
        if not super().__eq__(other) or not isinstance(other, CompoundTag):
            return False
        return self.definition == other.definition
