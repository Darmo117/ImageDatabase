from __future__ import annotations

import abc
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW
import pyperclip

from . import components, flow_layout
from .. import config, model, utils
from ..i18n import translate as _t

SelectionChangeListener = typ.Callable[[typ.Iterable[model.Image]], None]
ItemDoubleClickListener = typ.Callable[[model.Image], None]


################
# Base classes #
################


class ImageItem:
    """An ImageItem is an item that holds an image."""

    def __init__(self):
        self._image = None

    @property
    def image(self) -> model.Image:
        """Returns the image."""
        return self._image


class ImageListView:
    def _init_contextual_menu(self):
        # noinspection PyTypeChecker
        self._menu = QtW.QMenu(parent=self)

        self._copy_paths_action = self._menu.addAction(
            utils.gui.icon('edit-copy'),
            _t('main_window.tab.context_menu.copy_path_item'),
            self.copy_image_paths,
            'Ctrl+C'
        )
        self._select_all_action = self._menu.addAction(
            utils.gui.icon('edit-select-all'),
            _t('menu_common.select_all_item'),
            self.select_all,
            'Ctrl+A'
        )

        # noinspection PyUnresolvedReferences
        self.setContextMenuPolicy(QtC.Qt.CustomContextMenu)
        # noinspection PyUnresolvedReferences
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._update_actions()

    def _show_context_menu(self):
        self._menu.exec_(QtG.QCursor.pos())

    def _update_actions(self):
        selected_items = len(self.selected_items())
        self._copy_paths_action.setDisabled(not selected_items)
        if selected_items > 1:
            self._copy_paths_action.setText(_t('main_window.tab.context_menu.copy_paths_item'))
        else:
            self._copy_paths_action.setText(_t('main_window.tab.context_menu.copy_path_item'))
        self._select_all_action.setDisabled(not self.count())

    def copy_image_paths(self):
        if self._copy_paths_action.isEnabled():
            text = '\n'.join([str(image.path) for image in self.selected_images()])
            pyperclip.copy(text)

    @abc.abstractmethod
    def select_all(self):
        pass

    @abc.abstractmethod
    def selected_items(self) -> typ.List[ImageItem]:
        """Returns selected items."""
        pass

    @abc.abstractmethod
    def selected_images(self) -> typ.List[model.Image]:
        """Returns selected images."""
        pass

    @abc.abstractmethod
    def selected_indexes(self) -> typ.List[int]:
        """Returns selected indexes sorted in ascending order."""
        pass

    @abc.abstractmethod
    def get_images(self) -> typ.List[model.Image]:
        """Returns all images from this list."""
        pass

    @abc.abstractmethod
    def item(self, row: int) -> ImageItem:
        pass

    @abc.abstractmethod
    def add_image(self, image: model.Image):
        """Adds an image to this list.

        :param image: The image to add.
        """
        pass

    @abc.abstractmethod
    def clear(self):
        """Empties this list."""
        pass

    @abc.abstractmethod
    def count(self) -> int:
        """Returns the number of items in this list."""
        pass


class ImageList(QtW.QListWidget, ImageListView):
    """This list displays image paths."""

    def __init__(self, on_selection_changed: SelectionChangeListener,
                 on_item_double_clicked: ItemDoubleClickListener,
                 parent: QtW.QWidget = None):
        """Creates an image list.

        :param on_selection_changed: Function called when the selection changes.
        :param on_item_double_clicked: Function called when an item is double-clicked.
        :param parent: The widget this list belongs to.
        """
        super().__init__(parent)
        self.setSelectionMode(QtW.QAbstractItemView.ExtendedSelection)
        self.selectionModel().selectionChanged.connect(lambda _: on_selection_changed(self.selected_images()))
        self.itemDoubleClicked.connect(lambda i: on_item_double_clicked(i.image))
        self._init_contextual_menu()
        self.model().rowsInserted.connect(self._update_actions)
        self.model().rowsRemoved.connect(self._update_actions)

    def clear(self):
        super().clear()
        self._update_actions()

    def keyPressEvent(self, event: QtG.QKeyEvent):
        """Overrides “Ctrl+C“ action."""
        if utils.gui.event_matches_action(event, self._select_all_action):
            self.select_all()
            event.ignore()
        if utils.gui.event_matches_action(event, self._copy_paths_action):
            self.copy_image_paths()
            event.ignore()
        super().keyPressEvent(event)

    def selectionChanged(self, selected: QtC.QItemSelection, deselected: QtC.QItemSelection):
        super().selectionChanged(selected, deselected)
        self._update_actions()

    def select_all(self):
        self.selectAll()

    def selected_items(self) -> typ.List[ImageItem]:
        return [self.item(i) for i in self.selected_indexes()]

    def selected_images(self) -> typ.List[model.Image]:
        return [self.item(i).image for i in self.selected_indexes()]

    def selected_indexes(self) -> typ.List[int]:
        return sorted(map(QtC.QModelIndex.row, self.selectedIndexes()))

    def get_images(self) -> typ.List[model.Image]:
        return [self.item(i).image for i in range(self.count())]

    def item(self, row: int) -> ImageItem:
        return super().item(row)

    def add_image(self, image: model.Image):
        self.addItem(_ImageListItem(self, image))


class _ImageListItem(QtW.QListWidgetItem, ImageItem):
    """This class is used as an item in the ImageList widget."""

    def __init__(self, parent: QtW.QListWidget, image: model.Image):
        """Creates an item with the given image.

        :param parent: The list this item belongs to.
        :param image: The image to associate to this item.
        """
        super().__init__(parent=parent)
        self.setText(str(image.path))
        self._image = image


class ThumbnailList(flow_layout.ScrollingFlowWidget, ImageListView):
    """This widget lists results returned by the user query as image thumbnails."""

    def __init__(self, on_selection_changed: SelectionChangeListener,
                 on_item_double_clicked: ItemDoubleClickListener,
                 parent: QtW.QWidget = None):
        """Creates an image list.

        :param on_selection_changed: Function called when the selection changes.
        :param on_item_double_clicked: Function called when an item is double-clicked.
        :param parent: The widget this list belongs to.
        """
        super().__init__(parent)
        self._selection_changed = on_selection_changed
        self._on_item_double_clicked = on_item_double_clicked
        self._last_index = -1
        self._init_contextual_menu()

    def _on_selection_changed(self):
        self._update_actions()
        self._selection_changed(self.selected_images())

    def select_all(self):
        for item in self._flow_layout.items:
            item.selected = True
        self._on_selection_changed()

    def selected_items(self) -> typ.List[ImageItem]:
        return [item for item in self._flow_layout.items if item.selected]

    def selected_images(self) -> typ.List[model.Image]:
        return [item.image for item in self._flow_layout.items if item.selected]

    def selected_indexes(self) -> typ.List[int]:
        return [i for i, item in enumerate(self._flow_layout.items) if item.selected]

    def get_images(self) -> typ.List[model.Image]:
        return [item.image for item in self._flow_layout.items]

    def item(self, index: int) -> ImageItem:
        return self._flow_layout.items[index]

    def add_image(self, image: model.Image):
        self.add_widget(_FlowImageItem(image, len(self._flow_layout.items), self._item_clicked,
                                       self._item_double_clicked))
        self._update_actions()

    def clear(self):
        self._flow_layout.clear()
        self._last_index = -1
        self._update_actions()

    def count(self) -> int:
        return self._flow_layout.count()

    def mousePressEvent(self, event: QtG.QMouseEvent):
        if event.button() != QtC.Qt.RightButton:
            self._last_index = -1
            self._deselect_except(None)
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QtG.QKeyEvent):
        """Handles “Ctrl+A“ and “Ctrl+C“ actions."""
        if utils.gui.event_matches_action(event, self._select_all_action):
            self.select_all()
            event.ignore()
        elif utils.gui.event_matches_action(event, self._copy_paths_action):
            self.copy_image_paths()
            event.ignore()
        super().keyPressEvent(event)

    def _item_clicked(self, item: _FlowImageItem):
        """Called when an item is clicked once. It handles Ctrl+Click and Shift+Click actions.

        :param item: The clicked item.
        """
        modifiers = QtW.QApplication.keyboardModifiers()
        if modifiers == QtC.Qt.ControlModifier:
            if item.selected:
                item.selected = False
                self._last_index = -1
            else:
                item.selected = True
                self._last_index = item.index
        elif modifiers == QtC.Qt.ShiftModifier:
            self._deselect_except(item)
            if self._last_index != -1:
                if self._last_index <= item.index:
                    items = self._flow_layout.items[self._last_index:item.index + 1]
                else:
                    items = self._flow_layout.items[item.index:self._last_index + 1]
                for i in items:
                    i.selected = True
            else:
                item.selected = True
                self._last_index = item.index
        else:
            self._last_index = item.index
            item.selected = True
            self._deselect_except(item)
        self._on_selection_changed()

    def _item_double_clicked(self, item: _FlowImageItem):
        self._deselect_except(item)
        item.selected = True
        self._last_index = item.index
        self._on_item_double_clicked(item.image)

    def _deselect_except(self, item: typ.Optional[_FlowImageItem]):
        """Deselects all items apart from the given one.

        :param item: The item to keep selected.
        """
        for i in self.selected_items():
            if i is not item:
                i.selected = False
        self._on_selection_changed()


class _FlowImageItem(QtW.QFrame, ImageItem):
    """An widget that displays an image and can be selected.
    Used by the ThumbnailList class to display images returned by the user query.
    """

    def __init__(self, image: model.Image, index: int, on_click: typ.Callable[[_FlowImageItem], None],
                 on_double_click: typ.Callable[[_FlowImageItem], None]):
        """Creates an image item.

        :param image: The image to display.
        :param index: Item's index.
        :param on_click: Function to call when this item is clicked.
        :param on_double_click: Function to call when this item is double-clicked.
        """
        super().__init__()

        self._image = image
        self._index = index

        self._on_click = on_click
        self._on_double_click = on_double_click

        layout = QtW.QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)

        self._image_view = components.Canvas(keep_border=False, show_errors=False, parent=self)
        # Allows file drag-and-drop
        self._image_view.dragEnterEvent = self.dragEnterEvent
        self._image_view.dragMoveEvent = self.dragMoveEvent
        self._image_view.dropEvent = self.dropEvent
        self._image_view.set_image(self._image.path)
        size = config.CONFIG.thumbnail_size
        self._image_view.setFixedSize(QtC.QSize(size, size))
        self._image_view.mousePressEvent = self.mousePressEvent
        self._image_view.mouseReleaseEvent = self.mouseReleaseEvent
        self._image_view.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        layout.addWidget(self._image_view)

        text = self._image.path.name
        label = components.EllipsisLabel(text, parent=self)
        label.setAlignment(QtC.Qt.AlignCenter)
        label.setFixedWidth(size)
        label.setToolTip(text)
        layout.addWidget(label)

        self.setLayout(layout)

        self.selected = False

    @property
    def index(self):
        return self._index

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        """Toggles selection. Border and background will turn blue whenever this item is selected."""
        self._selected = value
        if self._selected:
            bg_color = QtW.QApplication.palette().color(QtG.QPalette.Active, QtG.QPalette.Highlight)
            fg_color = QtW.QApplication.palette().color(QtG.QPalette.Active, QtG.QPalette.HighlightedText)
        else:
            bg_color = QtW.QApplication.palette().color(QtG.QPalette.Normal, QtG.QPalette.Window)
            fg_color = QtW.QApplication.palette().color(QtG.QPalette.Normal, QtG.QPalette.WindowText)
        self.setStyleSheet(f'background-color: {bg_color.name()}; color: {fg_color.name()}')

    def mousePressEvent(self, event: QtG.QMouseEvent):
        # Do not deselect other items if right click on already selected item
        if event.button() != QtC.Qt.RightButton or not self._selected:
            self._on_click(self)

    def mouseDoubleClickEvent(self, event: QtG.QMouseEvent):
        self._on_double_click(self)
