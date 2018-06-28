import re
import typing as typ

import PyQt5.QtGui as QtG


class Image:
    """This class represents an image."""

    def __init__(self, ident: int, path: str):
        """
        Creates an image.

        :param ident: Image's SQLite ID.
        :param path: Image's path.
        """
        self._id = ident
        self._path = path

    @property
    def id(self) -> int:
        """Return this image's SQLite ID."""
        return self._id

    @property
    def path(self) -> str:
        """Returns this image's path."""
        return self._path

    def __repr__(self):
        return "Image[id=" + str(self._id) + ", path=" + self._path + "]"

    def __eq__(self, other):
        if not isinstance(other, Image):
            return False
        return self._id == other.id and self._path == other.path


class TagType:
    """This class represents a tag type."""
    SYMBOL_PATTERN = re.compile(r"^[^\w+()-]$")
    SYMBOL_TYPES = {}
    ID_TYPES = {}

    def __init__(self, ident: int, label: str, symbol: str, color: QtG.QColor = QtG.QColor(0, 0, 0)):
        """
        Creates a tag type.

        :param ident: Type's SQLite ID.
        :param label: Type's label.
        :param symbol: Type's symbol.
        :param color: Type's color.
        """
        self._id = ident
        self._label = label
        self._symbol = symbol
        self._color = color

    @property
    def id(self) -> int:
        """Returns this type's ID."""
        return self._id

    @property
    def label(self) -> str:
        """Returns this type's label."""
        return self._label

    @property
    def symbol(self) -> str:
        """Returns this type's symbol."""
        return self._symbol

    @property
    def color(self) -> QtG.QColor:
        """Returns this type's color."""
        return self._color

    def __eq__(self, other):
        if not isinstance(other, TagType):
            return False
        return (self.id == other.id and self.label == other.label and self.symbol == other.symbol and
                self._color == other.color)

    @staticmethod
    def init(types):
        """
        Initializes all available tag types.

        :param List[TagType] types: The available types.
        """
        TagType.SYMBOL_TYPES.clear()
        TagType.ID_TYPES.clear()
        for tag_type in types:
            TagType.SYMBOL_TYPES[tag_type.symbol] = tag_type
            TagType.ID_TYPES[tag_type.id] = tag_type

    @staticmethod
    def is_special_char(c: str) -> bool:
        """
        Tells if a character is a type symbol.

        :param c: The character to check.
        :return: True if the argument is a type symbol.
        """
        return c in TagType.SYMBOL_TYPES

    @staticmethod
    def from_symbol(symbol: str):
        """
        Returns the type with from the given symbol.

        :param symbol: The type symbol.
        :return: The corresponding type.
        :rtype: TagType
        """
        return TagType.SYMBOL_TYPES[symbol]

    @staticmethod
    def from_id(ident: int):
        """
        Returns the type with the given ID.

        :param ident: The SQLite ID.
        :return: The corresponding type.
        :rtype: TagType
        """
        return TagType.ID_TYPES[ident]


class Tag:
    """This class represents an image tag. Tags can be associated to a type."""
    TAG_PATTERN = re.compile(r"^\w+$")

    def __init__(self, ident: int, label: str, tag_type: typ.Optional[TagType] = None):
        """
        Creates a tag with an optional type.

        :param ident: Tag's SQLite ID.
        :param label: Tag's label.
        :param tag_type: Tag's type?
        """
        if not Tag.TAG_PATTERN.match(label):
            raise ValueError("Illegal tag format!")

        self._id = ident
        self._label = label
        self._type = tag_type

    def raw_label(self) -> str:
        """Returns the raw label, i.e. the name prefixed with its type symbol."""
        symbol = self._type.symbol if self._type is not None else ""
        return symbol + self._label

    @property
    def id(self) -> int:
        """Returns this tag's SQLite ID."""
        return self._id

    @property
    def label(self) -> str:
        """Return this tag's label."""
        return self._label

    @property
    def type(self) -> TagType:
        """Returns this tag's type."""
        return self._type

    def __repr__(self):
        return self._label

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False
        return self.id == other.id and self.label == other.label and self.type == other.type

    @classmethod
    def from_string(cls, s: str):
        """
        Returns a tag instance from a given string.

        :param s: The string to parse.
        :return: The corresponding tag.
        :rtype: Tag
        """
        has_type = TagType.is_special_char(s[0])
        label = s[1:] if has_type else s
        tag_type = TagType.from_symbol(s[0]) if has_type else None
        return cls(0, label, tag_type)
