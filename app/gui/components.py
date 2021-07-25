import os
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

from .. import model, utils
from ..i18n import translate as _t


class TagTree(QtW.QTreeWidget):
    """This class is a tree for tags. Nodes are created for each tag type and tags are added under the node of the
    corresponding type.
    """

    def __init__(self, parent: typ.Optional[QtW.QWidget] = None):
        """Creates a tag tree widget.

        :param parent: The widget this tree belongs to.
        """
        super().__init__(parent)
        self.setHeaderLabel(_t('main_window.tags_tree.title', amount=0))

    def refresh(self, types: typ.List[model.TagType], tags: typ.List[model.Tag]):
        """Refreshes this tree with the given tag types and tags. Tags without a type or with a type not present in the
        list are added under the “Unclassified” type node.

        :param types: Tag types.
        :param tags: Tags.
        """
        self.clear()
        types = sorted(types, key=lambda t: t.label)
        tags = sorted(tags, key=lambda t: t.label)

        self.setHeaderLabel(_t('main_window.tags_tree.title', amount=len(tags)))

        type_nodes = {}
        for tag_type in types:
            node = QtW.QTreeWidgetItem(self, [tag_type.label + ' (' + tag_type.symbol + ')'])
            node.setForeground(0, tag_type.color)
            font = QtG.QFont()
            font.setWeight(QtG.QFont.Bold)
            node.setFont(0, font)
            type_nodes[tag_type.id] = node
        default_type_node = QtW.QTreeWidgetItem(self, [_t('main_window.tags_tree.type_item_unclassified')])

        for tag in tags:
            if tag.type is None or tag.type.id not in type_nodes:
                item = QtW.QTreeWidgetItem(default_type_node, [tag.label])
            else:
                item = QtW.QTreeWidgetItem(type_nodes[tag.type.id], [tag.label])
            if isinstance(tag, model.CompoundTag):
                font = QtG.QFont()
                font.setItalic(True)
                item.setFont(0, font)
            item.setWhatsThis(0, 'tag')

        for node in type_nodes.values():
            node.setText(0, node.text(0) + f' [{node.childCount()}]')

        if default_type_node.childCount() == 0:
            default_type_node.setHidden(True)
        else:
            default_type_node.setText(0, default_type_node.text(0) + f' [{default_type_node.childCount()}]')


class Canvas(QtW.QGraphicsView):
    """This class is a canvas in which images can be displayed."""

    def __init__(self, keep_border: bool = True, show_errors: bool = True):
        """Creates an empty canvas with no image.

        :param keep_border: If true the default border and bakground will be kept;
                            otherwise they will both be transparent unless there is no image.
        :param show_errors: If true a popup will appear when an image cannot be loaded.
        """
        super().__init__()
        self._image = None
        self._keep_border = keep_border
        self._show_errors = show_errors

    def set_image(self, image_path: str):
        """Sets the image to display.

        :param image_path: Path to the image.
        """
        self.setScene(QtW.QGraphicsScene())
        if os.path.exists(image_path):
            ext = os.path.splitext(image_path)[1]
            self._image = QtG.QPixmap(image_path, format=ext)
            self.scene().addPixmap(self._image)
            self.fit()
            border = 0
        else:
            if self._show_errors:
                utils.show_error(_t('canvas.image_load_error'), parent=self)
            self._image = None
            self.scene().addText(_t('canvas.no_image'))
            border = '1px solid gray'

        if not self._keep_border:
            self.setStyleSheet(f'border: {border}; background-color: transparent')

    def fit(self):
        """Fits the image into the canvas."""
        if self._image is not None and not self.rect().contains(self._image.rect()):
            self.fitInView(self.scene().sceneRect(), QtC.Qt.KeepAspectRatio)

    def resizeEvent(self, event: QtG.QResizeEvent):
        self.fit()
        return super().resizeEvent(event)


class EllipsisLabel(QtW.QLabel):
    """This custom label adds an ellipsis (…) if the text doesn’t fit."""

    def paintEvent(self, event: QtG.QPaintEvent):
        painter = QtG.QPainter()
        painter.begin(self)
        self._draw_text(event, painter)
        painter.end()

    def _draw_text(self, event: QtG.QPaintEvent, painter: QtG.QPainter):
        metrics = QtG.QFontMetrics(self.font())
        elided_text = metrics.elidedText(self.text(), QtC.Qt.ElideRight, self.width())
        painter.drawText(event.rect(), QtC.Qt.AlignCenter, elided_text)


# Base code: https://blog.elentok.com/2011/08/autocomplete-textbox-for-multiple.html
# Code repo: https://bit.ly/3iOzAzA
class AutoCompleteLineEdit(QtW.QLineEdit):
    """LineEdit widget with built-in auto-complete."""
    _SEPARATOR = ' '

    def __init__(self):
        super().__init__()
        self._completer = QtW.QCompleter()
        self._completer.setCaseSensitivity(QtC.Qt.CaseInsensitive)
        self._completer.setFilterMode(QtC.Qt.MatchStartsWith)
        self._completer.setWidget(self)
        self._completer.activated.connect(self._insert_completion)
        self._keys_to_ignore = [QtC.Qt.Key_Enter, QtC.Qt.Key_Return]

    def set_completer_model(self, values: typ.Iterable[str]):
        self._completer.setModel(QtC.QStringListModel(values))

    def keyPressEvent(self, event):
        if self._completer.popup().isVisible() and event.key() in self._keys_to_ignore:
            event.ignore()
            return

        super().keyPressEvent(event)
        completion_prefix = self._text_under_cursor()
        if completion_prefix != self._completer.completionPrefix():
            self._update_completer_popup_items(completion_prefix)
        if len(event.text()) > 0 and len(completion_prefix) > 0:
            self._completer.complete()
        if len(completion_prefix) == 0:
            self._completer.popup().hide()

    def _insert_completion(self, completion: str):
        cp = self.cursorPosition()
        text = self.text()
        extra_length = len(completion) - len(self._completer.completionPrefix())
        if extra_length:
            extra_text = completion[-extra_length:]
            new_text = text[:cp] + extra_text
            remaining_text = text[cp:]
            if not remaining_text or remaining_text[0] != self._SEPARATOR:
                new_text += self._SEPARATOR
            self.setText(new_text + remaining_text)
            self.setCursorPosition(len(new_text))

    def _update_completer_popup_items(self, completion_prefix: str):
        """Filters the completer’s popup items to only show items with the given prefix."""
        self._completer.setCompletionPrefix(completion_prefix)
        self._completer.popup().setCurrentIndex(self._completer.completionModel().index(0, 0))

    def _text_under_cursor(self) -> str:
        text = self.text()
        text_under_cursor = ''
        i = self.cursorPosition() - 1

        while i >= 0 and text[i] != self._SEPARATOR:
            text_under_cursor = text[i] + text_under_cursor
            i -= 1

        return text_under_cursor
