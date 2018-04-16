import re

from PyQt5.QtGui import QColor


class Image:
    def __init__(self, id, path):
        self._id = id
        self._path = path

    @property
    def id(self):
        return self._id

    @property
    def path(self):
        return self._path

    def __str__(self):
        return "Image[id=" + str(self._id) + ", path=" + self._path + "]"

    def __eq__(self, other):
        if not isinstance(other, Image):
            return False
        return self._id == other.id and self._path == other.path


class Tag:
    TAG_PATTERN = re.compile(r"^\w+$")

    def __init__(self, id, label, type=None):
        if not Tag.TAG_PATTERN.match(label):
            raise ValueError("Illegal tag format!")

        self._id = id
        self._label = label
        self._type = type

    def raw_label(self):
        symbol = self._type.symbol if self._type is not None else ""
        return symbol + self._label

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def type(self):
        return self._type

    def __str__(self):
        return self._label

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False
        return self.id == other.id and self.label == other.label and self.type == other.type

    @classmethod
    def from_string(cls, s):
        has_type = TagType.is_special_char(s[0])
        label = s[1:] if has_type else s
        type = TagType.from_symbol(s[0]) if has_type else None
        return cls(0, label, type)


class TagType:
    SYMBOL_PATTERN = re.compile(r"^[^\w+()-]$")
    SYMBOL_TYPES = {}
    ID_TYPES = {}

    def __init__(self, id, label, symbol, color: QColor = QColor(0, 0, 0)):
        self._id = id
        self._label = label
        self._symbol = symbol
        self._color = color

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def symbol(self):
        return self._symbol

    @property
    def color(self):
        return self._color

    def __eq__(self, other):
        if not isinstance(other, TagType):
            return False
        return self.id == other.id and self.label == other.label and self.symbol == other.symbol and \
            self._color == other.color

    @staticmethod
    def init(types):
        TagType.SYMBOL_TYPES.clear()
        TagType.ID_TYPES.clear()
        for type in types:
            TagType.SYMBOL_TYPES[type.symbol] = type
            TagType.ID_TYPES[type.id] = type

    @staticmethod
    def is_special_char(c):
        return c in TagType.SYMBOL_TYPES

    @staticmethod
    def from_symbol(symbol):
        return TagType.SYMBOL_TYPES[symbol]

    @staticmethod
    def from_id(id):
        return TagType.ID_TYPES[id]
