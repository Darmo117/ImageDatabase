from __future__ import annotations

import pathlib
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW
import pyperclip

from .. import model, utils
from ..i18n import translate as _t


class TagTree(QtW.QTreeWidget):
    """This class is a tree for tags. Nodes are created for each tag type and tags are added under the node of the
    corresponding type.
    """
    TAG = 'tag'
    TAG_TYPE = 'tag_type'
    DATA_OBJECT = QtC.Qt.UserRole

    def __init__(self, on_delete_item: typ.Callable[[QtW.QTreeWidgetItem], None],
                 on_insert_tag: typ.Callable[[QtW.QTreeWidgetItem], None],
                 parent: typ.Optional[QtW.QWidget] = None):
        """Creates a tag tree widget.

        :param parent: The widget this tree belongs to.
        """
        super().__init__(parent)
        self.setHeaderLabel(_t('main_window.tags_tree.title', amount=0))

        self._delete_item = on_delete_item
        self._insert_tag = on_insert_tag

        self.itemDoubleClicked.connect(self._on_insert_tag)

        self._menu = QtW.QMenu(parent=self)

        self._copy_all_tags_action = self._menu.addAction(
            utils.gui.icon('edit-copy'),
            _t('main_window.tags_tree.context_menu.copy_all_item'),
            self._on_copy_all,
            'Ctrl+Shift+C'
        )
        self._copy_tags_action = self._menu.addAction(
            utils.gui.icon('edit-copy'),
            _t('main_window.tags_tree.context_menu.copy_tags_item'),
            self._on_copy_tags,
            'Ctrl+Alt+C'
        )
        self._copy_label_action = self._menu.addAction(
            utils.gui.icon('edit-copy'),
            _t('menu_common.copy_item'),
            self._on_copy_label,
            'Ctrl+C'
        )

        self._menu.addSeparator()

        self._delete_item_action = self._menu.addAction(
            utils.gui.icon('tag-delete'),
            _t('main_window.tags_tree.context_menu.delete_tag_item'),
            self._on_delete_item,
            'Delete'
        )

        self._menu.addSeparator()

        self._insert_tag_action = self._menu.addAction(
            utils.gui.icon('insert-text'),
            _t('main_window.tags_tree.context_menu.insert_tag_item'),
            self._on_insert_tag
        )
        self._insert_tag_action.setShortcuts(['Return', 'Num+Enter'])

        self.setContextMenuPolicy(QtC.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._update_actions()

    def _show_context_menu(self):
        self._menu.exec_(QtG.QCursor.pos())

    def _update_actions(self):
        selected_items = self.selectedItems()
        item = selected_items[0] if selected_items else None
        item_type = item.whatsThis(0) if item else None
        self._copy_tags_action.setDisabled(not selected_items or item_type != self.TAG_TYPE)
        self._copy_label_action.setDisabled(not selected_items)
        self._delete_item_action.setDisabled(not selected_items or item.data(0, self.DATA_OBJECT) is None)
        if item_type == self.TAG_TYPE:
            self._delete_item_action.setText(_t('main_window.tags_tree.context_menu.delete_tag_type_item'))
        else:
            self._delete_item_action.setText(_t('main_window.tags_tree.context_menu.delete_tag_item'))
        self._insert_tag_action.setDisabled(not selected_items or item_type != self.TAG)

    def _on_copy_all(self):
        text = ''
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if i != 0:
                text += '\n'
            text += self.get_item_label(item, keep_symbols=True) + '\n'
            text += '\n'.join(['\t' + self.get_item_label(item.child(j)) for j in range(item.childCount())])
        if text:
            pyperclip.copy(text)

    def _on_copy_tags(self):
        if self._copy_tags_action.isEnabled():
            item = self.selectedItems()[0]
            if item.whatsThis(0) == self.TAG_TYPE:
                text = self.get_item_label(item, keep_symbols=True) + '\n'
                text += '\n'.join(['\t' + self.get_item_label(item.child(i)) for i in range(item.childCount())])
                pyperclip.copy(text)

    def _on_copy_label(self):
        if self._copy_label_action.isEnabled():
            pyperclip.copy(self.get_item_label(self.selectedItems()[0], keep_symbols=True))

    def _on_delete_item(self):
        if self._delete_item_action.isEnabled():
            self._delete_item(self.selectedItems()[0])

    def _on_insert_tag(self, *_):
        if self._insert_tag_action.isEnabled():
            self._insert_tag(self.selectedItems()[0])

    def keyPressEvent(self, event: QtG.QKeyEvent):
        if utils.gui.event_matches_action(event, self._copy_all_tags_action):
            self._on_copy_all()
            event.ignore()
        elif utils.gui.event_matches_action(event, self._copy_tags_action):
            self._on_copy_tags()
            event.ignore()
        elif utils.gui.event_matches_action(event, self._copy_label_action):
            self._on_copy_label()
            event.ignore()
        elif utils.gui.event_matches_action(event, self._delete_item_action):
            self._on_delete_item()
            event.ignore()
        elif utils.gui.event_matches_action(event, self._insert_tag_action):
            self._on_insert_tag()
            event.ignore()
        super().keyPressEvent(event)

    def selectionChanged(self, selected: QtC.QItemSelection, deselected: QtC.QItemSelection):
        super().selectionChanged(selected, deselected)
        self._update_actions()

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
            node.setWhatsThis(0, self.TAG_TYPE)
            node.setData(0, self.DATA_OBJECT, tag_type)
            type_nodes[tag_type.id] = node
        default_type_node = QtW.QTreeWidgetItem(self, [_t('main_window.tags_tree.type_item_unclassified')])
        default_type_node.setWhatsThis(0, self.TAG_TYPE)
        default_type_node.setData(0, self.DATA_OBJECT, None)

        for tag in tags:
            if tag.type is None or tag.type.id not in type_nodes:
                item = QtW.QTreeWidgetItem(default_type_node, [tag.label])
            else:
                item = QtW.QTreeWidgetItem(type_nodes[tag.type.id], [tag.label])
            if isinstance(tag, model.CompoundTag):
                font = QtG.QFont()
                font.setItalic(True)
                item.setFont(0, font)
            item.setWhatsThis(0, self.TAG)
            item.setData(0, self.DATA_OBJECT, tag)

        for node in type_nodes.values():
            node.setText(0, node.text(0) + f' [{node.childCount()}]')

        if default_type_node.childCount() == 0:
            default_type_node.setHidden(True)
        else:
            default_type_node.setText(0, default_type_node.text(0) + f' [{default_type_node.childCount()}]')

    @staticmethod
    def get_item_label(item: QtW.QTreeWidgetItem, keep_symbols: bool = False) -> str:
        """Returns the label for the given tree item.

        :param item: The item.
        :param keep_symbols: If True and the item represents a tag type,
            the tag type symbol will be returned along with the label.
        :return: The item’s label.
        """
        o: typ.Union[model.Tag, model.TagType] = item.data(0, TagTree.DATA_OBJECT)
        if item.whatsThis(0) == TagTree.TAG_TYPE:
            if o:
                return o.label + (f' ({o.symbol})' if keep_symbols else '')
            else:
                return _t('main_window.tags_tree.type_item_unclassified')
        return o.label


class Canvas(QtW.QGraphicsView):
    """This class is a canvas in which images can be displayed."""

    def __init__(self, keep_border: bool = True, show_errors: bool = True, parent: QtW.QWidget = None):
        """Creates an empty canvas with no image.

        :param keep_border: If true the default border and bakground will be kept;
                            otherwise they will both be transparent unless there is no image.
        :param show_errors: If true a popup will appear when an image cannot be loaded.
        :param parent: This widget’s parent.
        """
        super().__init__(parent=parent)
        self._image = None
        self._keep_border = keep_border
        self._show_errors = show_errors

    def set_image(self, image_path: pathlib.Path):
        """Sets the image to display.

        :param image_path: Path to the image.
        """
        self.setScene(QtW.QGraphicsScene())
        if image_path.exists():
            ext = utils.files.get_extension(image_path.name, keep_dot=True)
            self._image = QtG.QPixmap(str(image_path), format=ext)
            reader = QtG.QImageReader(str(image_path))
            if reader.imageCount() <= 1:
                self.scene().addPixmap(self._image)
            else:
                gif_anim = QtW.QLabel()  # Must not set parent
                movie = QtG.QMovie(str(image_path), parent=gif_anim)
                gif_anim.setMovie(movie)
                movie.start()
                self.scene().addWidget(gif_anim)
            self.fit()
            border = '0'
        else:
            if self._show_errors:
                utils.gui.show_error(_t('canvas.image_load_error'), parent=self)
            self._image = None
            self.scene().addText(_t('canvas.no_image'))
            border = '1px solid gray'

        if not self._keep_border:
            self.setStyleSheet(f'border: {border}')

    def fit(self):
        """Fits the image into the canvas."""
        if self._image:
            if not self.rect().contains(self._image.rect()):
                self.fitInView(self.scene().sceneRect(), QtC.Qt.KeepAspectRatio)
            else:
                self.fitInView(QtC.QRectF(self.rect()), QtC.Qt.KeepAspectRatio)

    def showEvent(self, event: QtG.QShowEvent):
        self.fit()
        return super().showEvent(event)

    def resizeEvent(self, event: QtG.QResizeEvent):
        self.fit()
        return super().resizeEvent(event)


class EllipsisLabel(QtW.QLabel):
    """This custom label adds an ellipsis (…) if the text doesn’t fit."""

    _on_click = None

    def __init__(self, text: str = '', parent: QtW.QWidget = None):
        super().__init__(text, parent=parent)
        self._elide_mode = QtC.Qt.ElideMiddle

    def set_elide_mode(self, mode: QtC.Qt.TextElideMode):
        self._elide_mode = mode

    def paintEvent(self, event: QtG.QPaintEvent):
        painter = QtG.QPainter()
        painter.begin(self)
        self._draw_text(event, painter)
        painter.end()

    def _draw_text(self, event: QtG.QPaintEvent, painter: QtG.QPainter):
        metrics = QtG.QFontMetrics(self.font())
        elided_text = metrics.elidedText(self.text(), self._elide_mode, self.width())
        # noinspection PyTypeChecker
        painter.drawText(event.rect(), self.alignment() | QtC.Qt.AlignVCenter, elided_text)

    def set_on_click(self, callback: typ.Callable[[EllipsisLabel], None]):
        self._on_click = callback

    def mouseReleaseEvent(self, event: QtG.QMouseEvent):
        if self._on_click:
            self._on_click(self)
        super().mouseReleaseEvent(event)


class LabelWithIcon(QtW.QWidget):
    """Wrapper widget that displays a label with an icon on its left."""

    def __init__(self, icon: QtG.QIcon = None, text: str = None, parent: QtW.QWidget = None):
        super().__init__(parent=parent)
        layout = QtW.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self._icon = QtW.QLabel(parent=self)
        if icon:
            self.setIcon(icon)
        layout.addWidget(self._icon)

        self._label = QtW.QLabel(parent=self)
        if text is not None:
            self.setText(text)
        layout.addWidget(self._label, stretch=1)

        self.setLayout(layout)

    # noinspection PyPep8Naming
    def setIcon(self, icon: QtG.QIcon = None):
        """Sets the icon."""
        if icon:
            self._icon.setPixmap(icon.pixmap(16))
        else:
            self._icon.clear()

    # noinspection PyPep8Naming
    def setText(self, text: str):
        """Sets the label text."""
        self._label.setText(text)

    def text(self) -> str:
        """Returns the label text."""
        return self._label.text()


class TranslatedLineEdit(QtW.QLineEdit):
    """QLineEdit with translated cell context menu."""

    def contextMenuEvent(self, event: QtG.QContextMenuEvent):
        menu = self.createStandardContextMenu()
        utils.gui.translate_text_widget_menu(menu)
        menu.exec_(event.globalPos())


class TranslatedPlainTextEdit(QtW.QPlainTextEdit):
    """QPlainTextEdit with translated cell context menu."""

    def contextMenuEvent(self, event: QtG.QContextMenuEvent):
        menu = self.createStandardContextMenu()
        utils.gui.translate_text_widget_menu(menu)
        menu.exec_(event.globalPos())


class TranslatedTableWidget(QtW.QTableWidget):
    """QTableWidget with translated cell context menu."""

    def __init__(self, parent: QtW.QWidget = None):
        super().__init__(parent=parent)
        self.setItemDelegate(self._StyledItemDelegate(parent=self))

    class _StyledItemDelegate(QtW.QStyledItemDelegate):
        def createEditor(self, parent, option, index):
            editor = super().createEditor(parent, option, index)
            if isinstance(editor, QtW.QLineEdit):
                editor.setContextMenuPolicy(QtC.Qt.CustomContextMenu)
                editor.customContextMenuRequested.connect(self.handle_context_menu)
            return editor

        def handle_context_menu(self, pos: QtC.QPoint):
            editor = self.sender()
            if isinstance(editor, QtW.QLineEdit):
                menu = editor.createStandardContextMenu()
                utils.gui.translate_text_widget_menu(menu)
                menu.exec_(editor.mapToGlobal(pos))


# Base code: https://blog.elentok.com/2011/08/autocomplete-textbox-for-multiple.html
# Code repo: https://bit.ly/3iOzAzA
class AutoCompleteLineEdit(TranslatedLineEdit):
    """LineEdit widget with built-in auto-complete."""
    _SEPARATOR = ' '

    def __init__(self, parent: QtW.QWidget = None):
        super().__init__(parent=parent)
        self._completer = QtW.QCompleter(parent=self)
        self._completer.setCaseSensitivity(QtC.Qt.CaseInsensitive)
        self._completer.setFilterMode(QtC.Qt.MatchStartsWith)
        self._completer.setWidget(self)
        self._completer.activated.connect(self._insert_completion)
        self._keys_to_ignore = [QtC.Qt.Key_Enter, QtC.Qt.Key_Return]

    def set_completer_model(self, values: typ.Iterable[str]):
        self._completer.setModel(QtC.QStringListModel(values, parent=self))

    def keyPressEvent(self, event: QtG.QKeyEvent):
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
            if cp < len(text) and text[cp] != self._SEPARATOR:
                extra_text += self._SEPARATOR
            self.insert(extra_text)

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


class IntLineEdit(TranslatedLineEdit):
    """Text input that only accepts integer values in a given range."""

    class Validator(QtG.QIntValidator):
        """Custom validator that brings outlying values back into the defined range."""

        def fixup(self, s: str) -> str:
            if not s:
                return str(self.bottom())
            i = int(s)
            if i < self.bottom():
                return str(self.bottom())
            elif i > self.top():
                return str(self.top())
            return s

    def __init__(self, bottom: int, top: int, parent: QtW.QWidget = None):
        """Text input that only accepts integer values in a given range.

        :param bottom: Minimum accepted value.
        :param top: Maximum accepted value.
        :param parent: Parent widget.
        """
        super().__init__(parent=parent)
        self.setValidator(self.Validator(bottom, top, parent=self))

    def set_value(self, i: int):
        """Sets the integer value."""
        self.setText(str(i))

    def value(self) -> typ.Optional[int]:
        """Returns the current value or None if it is not an integer."""
        try:
            return int(self.text())
        except ValueError:
            return None

    def keyPressEvent(self, event: QtG.QKeyEvent):
        if event.key() == QtC.Qt.Key_Up and self.value() is not None and self.value() < self.validator().top():
            self.set_value(self.value() + 1)
            event.ignore()
        elif event.key() == QtC.Qt.Key_Down and self.value() is not None and self.value() > self.validator().bottom():
            self.set_value(self.value() - 1)
            event.ignore()
        super().keyPressEvent(event)


class CommandLineWidget(QtW.QWidget):
    _HISTORY_LIMIT = 2000

    def __init__(self, parent: QtW.QWidget = None):
        super().__init__(parent=parent)
        self._default_color = QtW.QApplication.palette().color(QtG.QPalette.Active, QtG.QPalette.Text)
        self._error_color = QtG.QColor(200, 0, 0)
        self._prompt_color = QtG.QColor(128, 128, 128)
        self._font_size = 14
        self._font_family = 'monospace'
        self._prompt = '$'

        self._callback = None
        self._input_history = []
        self._current_input = ''
        self._history_index = -1

        layout = QtW.QVBoxLayout()

        self._output = self._OutputField(parent=self)
        self._output.setAcceptRichText(True)
        self._output.setReadOnly(True)
        layout.addWidget(self._output, stretch=1)

        self._input = self._InputField(parent=self)
        self._input.textEdited.connect(self._save_input)
        self._input.enter_pressed.connect(self._on_input)
        self._input.cleared_triggered.connect(self._output.clear)
        self._input.up_pressed.connect(self._history_up)
        self._input.down_pressed.connect(self._history_down)
        layout.addWidget(self._input)

        self.setLayout(layout)

        self._update_style_sheet()

    def setFocus(self):
        self._input.setFocus()

    def set_input_placeholder(self, s: str):
        self._input.setPlaceholderText(s)

    def set_input_tooltip(self, s: str):
        self._input.setToolTip(s)

    def set_error_color(self, color: QtG.QColor):
        self._error_color = color
        self._update_style_sheet()

    def set_prompt_color(self, color: QtG.QColor):
        self._prompt_color = color
        self._update_style_sheet()

    def set_default_color(self, color: QtG.QColor):
        self._default_color = color
        self._update_style_sheet()

    def set_font_size(self, size: int):
        self._font_size = size
        self._update_style_sheet()

    def set_font_family(self, family: str):
        self._font_family = family
        self._update_style_sheet()

    def set_prompt(self, s: str):
        self._prompt = s

    def set_input_callback(self, callback: typ.Callable[[str], None]):
        self._callback = callback

    def print(self, *text, sep: str = ' ', end: str = '\n'):
        self._print(*text, sep=sep, end=end, mode=self._PRINT_NORMAL)

    def print_error(self, *text, sep: str = ' ', end: str = '\n'):
        self._print(*text, sep=sep, end=end, mode=self._PRINT_ERROR)

    _PRINT_NORMAL = 0
    _PRINT_ERROR = 1
    _PRINT_PROMPT = 2

    def _print(self, *text, sep: str = ' ', end: str = '\n', mode: int):
        self._output.moveCursor(QtG.QTextCursor.End)
        line = sep.join(map(str, text)) + end
        if mode == self._PRINT_ERROR:
            self._output.insertHtml(f'<span class="error">{line}</span>')
        elif mode == self._PRINT_PROMPT:
            self._output.insertHtml(f'<span class="prompt">{line}</span>')
        elif mode == self._PRINT_NORMAL:
            self._output.insertHtml(f'<span class="normal">{line}</span>')

    def _on_input(self, s: str):
        self._input.clear()
        self._print(self._prompt, s, mode=self._PRINT_PROMPT)
        if not self._input_history or s != self._input_history[0]:
            self._input_history.insert(0, s)
            if len(self._input_history) == self._HISTORY_LIMIT:
                self._input_history.pop(-1)
        self._history_index = -1
        if self._callback:
            self._callback(s)

    def _save_input(self, text: str):
        self._current_input = text

    def _history_up(self):
        if self._input_history:
            if self._history_index < len(self._input_history) - 1:
                self._history_index += 1
                self._input.setText(self._input_history[self._history_index])

    def _history_down(self):
        if self._input_history:
            if self._history_index > 0:
                self._history_index -= 1
                self._input.setText(self._input_history[self._history_index])
            elif self._history_index == 0:
                self._history_index = -1
                self._input.setText(self._current_input)

    def _update_style_sheet(self):
        self._output.document().setDefaultStyleSheet(f"""
        * {{
            white-space: pre;
            font-size: {self._font_size}px;
            font-family: {self._font_family}, "Courier New", monospace;
        }}

        .error {{
            color: {self._error_color.name()};
            font-weight: bold;
        }}

        .prompt {{
            color: {self._prompt_color.name()};
            font-weight: bold;
        }}

        .normal {{
            color: {self._default_color.name()};
        }}
        """.strip())
        self._input.setStyleSheet(
            f'font-size: {self._font_size}px; font-family: {self._font_family}, "Courier New", monospace;')

    class _OutputField(QtW.QTextEdit):
        def __init__(self, parent: QtW.QWidget = None):
            super().__init__(parent=parent)
            self._menu = self.createStandardContextMenu()

            self._menu.removeAction(self._menu.actions()[6])  # Delete
            self._menu.removeAction(self._menu.actions()[5])  # Paste
            self._menu.removeAction(self._menu.actions()[3])  # Cut
            self._menu.removeAction(self._menu.actions()[2])  # Separator
            self._menu.removeAction(self._menu.actions()[1])  # Redo
            self._menu.removeAction(self._menu.actions()[0])  # Undo

            self._copy_action = self._menu.actions()[0]
            self._copy_action.setText(_t('menu_common.copy_item'))
            self._copy_action.setIcon(utils.gui.icon('edit-copy'))
            self._copy_action.setShortcut('Ctrl+C')

            self._clear_action = QtW.QAction(
                utils.gui.icon('edit-clear-history'),
                _t('command_line.menu.clear_item'),
                parent=self
            )
            self._clear_action.setShortcut('Ctrl+L')
            self._clear_action.triggered.connect(self.clear)
            self._menu.insertAction(self._menu.actions()[1], self._clear_action)

            self._select_all_action = self._menu.actions()[3]
            self._select_all_action.setText(_t('menu_common.select_all_item'))
            self._select_all_action.setIcon(utils.gui.icon('edit-select-all'))
            self._select_all_action.setShortcut('Ctrl+A')

            self.textChanged.connect(self._update_menu)
            self.selectionChanged.connect(self._update_menu)

            self._update_menu()

        def contextMenuEvent(self, event: QtG.QContextMenuEvent):
            self._menu.exec_(QtG.QCursor.pos())

        def _update_menu(self):
            text = self.toPlainText()
            self._copy_action.setDisabled(not self.textCursor().selection().toPlainText())
            self._clear_action.setDisabled(not text)
            self._select_all_action.setDisabled(not text)

    class _InputField(TranslatedLineEdit):
        enter_pressed = QtC.pyqtSignal(str)
        cleared_triggered = QtC.pyqtSignal()
        up_pressed = QtC.pyqtSignal()
        down_pressed = QtC.pyqtSignal()

        def __init__(self, parent: QtW.QWidget = None):
            super().__init__(parent=parent)

        def keyPressEvent(self, event: QtG.QKeyEvent):
            # noinspection PyProtectedMember
            if event.key() in [QtC.Qt.Key_Return, QtC.Qt.Key_Enter]:
                self.enter_pressed.emit(self.text())
                event.ignore()
            elif utils.gui.event_matches_action(event, self.parent()._output._clear_action):
                self.cleared_triggered.emit()
                event.ignore()
            elif event.key() == QtC.Qt.Key_Up:
                self.up_pressed.emit()
                event.ignore()
            elif event.key() == QtC.Qt.Key_Down:
                self.down_pressed.emit()
                event.ignore()
            super().keyPressEvent(event)
