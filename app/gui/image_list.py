from __future__ import annotations

import abc
import os
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

from .components import Canvas, EllipsisLabel
from .flow_layout import ScrollingFlowWidget
from .. import config, constants, model

SelectionChangeListener = typ.Callable[[typ.Tuple[model.Image]], None]
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
        """Returns selected indexes."""
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
        """
        Adds an image to this list.

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

    def __init__(self, selection_change_listener: SelectionChangeListener,
                 item_double_click_listener: ItemDoubleClickListener,
                 parent: QtW.QWidget = None,
                 drop_action: typ.Callable[[typ.List[str]], None] = None):
        """
        Creates an image list.

        :param parent: The widget this list belongs to.
        :param drop_action: The action to perform when files are dropped into this list.
        """
        super().__init__(parent)
        self.setSelectionMode(QtW.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        # noinspection PyUnresolvedReferences, PyTypeChecker
        self.selectionModel().selectionChanged.connect(lambda _: selection_change_listener(self.selected_images()))
        # noinspection PyUnresolvedReferences
        self.itemDoubleClicked.connect(lambda i: item_double_click_listener(i.image))
        self._drop_action = drop_action

    def selected_items(self) -> typ.List[ImageItem]:
        return [self.item(i.row()) for i in self.selectedIndexes()]

    def selected_images(self) -> typ.List[model.Image]:
        return [self.item(i.row()).image for i in self.selectedIndexes()]

    def selected_indexes(self) -> typ.List[int]:
        return self.selectedIndexes()

    def get_images(self) -> typ.List[model.Image]:
        return [self.item(i).image for i in range(self.count())]

    def item(self, row: int) -> ImageItem:
        return super().item(row)

    def add_image(self, image: model.Image):
        self.addItem(_ImageListItem(self, image))

    def dragEnterEvent(self, event: QtG.QDragEnterEvent):
        self._check_drag(event)

    def dragMoveEvent(self, event: QtG.QDragMoveEvent):
        self._check_drag(event)

    def dropEvent(self, event: QtG.QDropEvent):
        if self._drop_action is not None:
            self._drop_action(self._get_urls(event))

    @staticmethod
    def _check_drag(event: QtG.QDragMoveEvent):
        """
        Checks the validity of files dragged into this list. If at least one file has an extension that is not in the
        config.FILE_EXTENSION array, the event is cancelled.

        :param event: The drag event.
        """
        if event.mimeData().hasUrls():
            try:
                urls = ImageList._get_urls(event)
            except ValueError:
                event.ignore()
            else:
                if all(map(lambda f: os.path.splitext(f)[1].lower()[1:] in constants.FILE_EXTENSIONS, urls)):
                    event.accept()
                else:
                    event.ignore()
        else:
            event.ignore()

    @staticmethod
    def _get_urls(event: QtG.QDropEvent) -> typ.List[str]:
        """
        Extracts all file URLs from the drop event.

        :param event: The drop event.
        :return: URLs of dropped files.
        """
        urls = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                raise ValueError("URL is not local!")
            urls.append(url.toLocalFile())
        return urls


class _ImageListItem(QtW.QListWidgetItem, ImageItem):
    """This class is used as an item in the ImageList widget."""

    def __init__(self, parent: QtW.QListWidget, image: model.Image):
        """
        Creates an item with the given image.

        :param parent: The list this item belongs to.
        :param image: The image to associate to this item.
        """
        super().__init__(parent=parent)
        self.setText(image.path)
        self._image = image


class ThumbnailList(ScrollingFlowWidget, ImageListView):
    """This widget lists results returned by the user query as image thumbnails."""

    def __init__(self, on_selection_changed: SelectionChangeListener,
                 on_item_double_clicked: ItemDoubleClickListener,
                 parent: QtW.QWidget = None):
        super().__init__(parent)
        self._on_selection_changed = on_selection_changed
        self._on_item_double_clicked = on_item_double_clicked
        self._last_index = -1

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

    def clear(self):
        self._flow_layout.clear()
        self._last_index = -1

    def count(self) -> int:
        return self._flow_layout.count()

    def mousePressEvent(self, _):
        self._last_index = -1
        self._deselect_except(None)

    def keyPressEvent(self, event: QtG.QKeyEvent):
        """Handles Ctrl+A action."""
        key = event.key()
        modifiers = event.modifiers()

        if key == QtC.Qt.Key_A and modifiers == QtC.Qt.ControlModifier:
            for item in self._flow_layout.items:
                item.selected = True
            # noinspection PyTypeChecker
            self._on_selection_changed(self.selected_images())

    def _item_clicked(self, item: _FlowImageItem):
        """
        Called when an item is clicked once. It handles Ctrl+Click and Shift+Click actions.

        :param item: The clicked item.
        """
        modifiers = QtW.QApplication.keyboardModifiers()
        # noinspection PyTypeChecker
        if modifiers & QtC.Qt.ControlModifier:
            if item.selected:
                item.selected = False
                self._last_index = -1
            else:
                item.selected = True
                self._last_index = item.index
        elif modifiers & QtC.Qt.ShiftModifier:
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
        # noinspection PyTypeChecker
        self._on_selection_changed(self.selected_images())

    def _item_double_clicked(self, item: _FlowImageItem):
        self._deselect_except(item)
        item.selected = True
        self._last_index = item.index
        self._on_item_double_clicked(item.image)

    def _deselect_except(self, item: typ.Optional[_FlowImageItem]):
        """
        Deselects all items apart from the given one.

        :param item: The item to keep selected.
        """
        for i in self.selected_items():
            if i is not item:
                i.selected = False
        # noinspection PyTypeChecker
        self._on_selection_changed(self.selected_images())


class _FlowImageItem(QtW.QWidget, ImageItem):
    """
    An widget that displays an image and can be selected.
    Used by the ThumbnailList class to display images returned by the user query.
    """

    def __init__(self, image: model.Image, index: int, on_click: typ.Callable[[_FlowImageItem], None],
                 on_double_click: typ.Callable[[_FlowImageItem], None]):
        """
        Creates an image item.

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

        self._image_view = Canvas(show_errors=False)
        self._image_view.set_image(self._image.path)
        size = config.CONFIG.thumbnail_size
        self._image_view.setFixedSize(QtC.QSize(size, size))
        self._image_view.mousePressEvent = self.mousePressEvent
        self._image_view.mouseReleaseEvent = self.mouseReleaseEvent
        self._image_view.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        layout.addWidget(self._image_view)

        text = os.path.basename(self._image.path)
        label = EllipsisLabel(text)
        label.setAlignment(QtC.Qt.AlignCenter)
        label.setFixedWidth(size)
        label.setToolTip(text)
        layout.addWidget(label)

        self.setLayout(layout)

        self._click_count = None
        self.selected = False

    @property
    def index(self):
        return self._index

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        """Toggles selection. Border will turn blue whenever this item is selected."""
        self._selected = value
        color = "blue" if self._selected else "white"
        self._image_view.setStyleSheet(f"border: 2px solid {color}")

    def mousePressEvent(self, event):
        self._click_count = 1

    def mouseDoubleClickEvent(self, event):
        self._click_count = 2
        self._on_double_click(self)

    def mouseReleaseEvent(self, event):
        if self._click_count == 1:
            # Delays the click action, waiting for an eventual second click.
            QtC.QTimer.singleShot(QtW.QApplication.instance().doubleClickInterval() // 4,
                                  self._perform_single_click_action)

    def _perform_single_click_action(self):
        if self._click_count == 1:
            self._on_click(self)
