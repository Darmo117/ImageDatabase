import os
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

import app.model as model
import app.utils as utils
import config


class ImageItem(QtW.QListWidgetItem):
    """An ImageItem is a list item that holds data of an image."""

    def __init__(self, parent: QtW.QListWidget, image: model.Image):
        """
        Creates an item with the given image.

        :param parent: The list this item belongs to.
        :param image: The image to associate to this item.
        """
        super().__init__(parent=parent)
        self.setText(image.path)
        self._image = image

    @property
    def image(self) -> model.Image:
        """Returns the image."""
        return self._image


class ImageList(QtW.QListWidget):
    """This list implementation displays image paths."""

    def __init__(self, parent: typ.Optional[QtW.QWidget] = None,
                 drop_action: typ.Optional[typ.Callable[[typ.List[str]], None]] = None):
        """
        Creates an image list.

        :param parent: The widget this list belongs to.
        :param drop_action: The action to perform when files are dropped into this list.
        """
        super().__init__(parent)
        self.setSelectionMode(QtW.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        self._drop_action = drop_action

    def add_image(self, image: model.Image):
        """
        Adds an image to this list.

        :param image: The image to add.
        """
        self.addItem(ImageItem(self, image))

    def get_images(self) -> typ.List[model.Image]:
        """Returns all images from this list."""
        # noinspection PyUnresolvedReferences
        return [self.item(i).image for i in range(self.count())]

    def selected_images(self) -> typ.List[model.Image]:
        """Returns selected images."""
        # noinspection PyUnresolvedReferences
        return [self.item(i.row()).image for i in self.selectedIndexes()]

    def dragEnterEvent(self, event: QtG.QDragEnterEvent):
        ImageList._check_drag(event)

    def dragMoveEvent(self, event: QtG.QDragMoveEvent):
        ImageList._check_drag(event)

    def dropEvent(self, event: QtG.QDropEvent):
        if self._drop_action is not None:
            self._drop_action(ImageList._get_urls(event))

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
                if all(map(lambda f: os.path.splitext(f)[1].lower()[1:] in config.FILE_EXTENSIONS, urls)):
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


class TagTree(QtW.QTreeWidget):
    """
    This class is a tree for tags. Nodes are created for each tag type and tags are added under the node of the
    corresponding type.
    """

    def __init__(self, parent: typ.Optional[QtW.QWidget] = None):
        """
        Creates a tag tree widget.

        :param parent: The widget this tree belongs to.
        """
        super().__init__(parent)
        self.setHeaderLabel("Tags")

    def refresh(self, types: typ.List[model.TagType], tags: typ.List[model.Tag]):
        """
        Refreshes this tree with the given tag types and tags. Tags without a type or with a type not present in the
        first argument are added under the 'Other' type node.

        :param types: Tag types.
        :param tags: Tags.
        """
        self.clear()
        types = sorted(types, key=lambda t: t.label)
        tags = sorted(tags, key=lambda t: t.label)

        type_nodes = {}
        for tag_type in types:
            node = QtW.QTreeWidgetItem(self, [tag_type.label + " (" + tag_type.symbol + ")"])
            node.setForeground(0, tag_type.color)
            font = QtG.QFont()
            font.setWeight(QtG.QFont.Bold)
            node.setFont(0, font)
            type_nodes[tag_type.id] = node
        default_type_node = QtW.QTreeWidgetItem(self, ["Other"])

        for tag in tags:
            if tag.type is None or tag.type.id not in type_nodes:
                item = QtW.QTreeWidgetItem(default_type_node, [tag.label])
            else:
                item = QtW.QTreeWidgetItem(type_nodes[tag.type.id], [tag.label])
            if isinstance(tag, model.CompoundTag):
                font = QtG.QFont()
                font.setItalic(True)
                item.setFont(0, font)
            item.setWhatsThis(0, "tag")
        if default_type_node.childCount() == 0:
            default_type_node.setHidden(True)


class Canvas(QtW.QGraphicsView):
    """This class is a canvas in which images can be displayed."""

    def __init__(self):
        """Creates an empty canvas with no image."""
        super().__init__()
        self._image = None

    def set_image(self, image_path: str):
        """
        Sets the image to display.

        :param image_path: Path to the image.
        """
        self.setScene(QtW.QGraphicsScene())
        if os.path.exists(image_path):
            ext = os.path.splitext(image_path)[1]
            self._image = QtG.QPixmap(image_path, format=ext)
            self.scene().addPixmap(self._image)
            self.fit()
        else:
            utils.show_error("Could not load image!", parent=self)
            self._image = None
            self.scene().addText("No image")

    def fit(self):
        """Fits the image into the canvas."""
        if self._image is not None and not self.rect().contains(self._image.rect()):
            self.fitInView(self.scene().sceneRect(), QtC.Qt.KeepAspectRatio)

    def resizeEvent(self, event: QtG.QResizeEvent):
        self.fit()
        return super().resizeEvent(event)


class EllipsisLabel(QtW.QLabel):
    """This custom label adds an ellipsis (…) if the text doesn't fit."""

    def paintEvent(self, event: QtG.QPaintEvent):
        painter = QtG.QPainter()
        painter.begin(self)
        self._draw_text(event, painter)
        painter.end()

    def _draw_text(self, event: QtG.QPaintEvent, painter: QtG.QPainter):
        metrics = QtG.QFontMetrics(self.font())
        elided_text = metrics.elidedText(self.text(), QtC.Qt.ElideRight, self.width())
        painter.drawText(event.rect(), QtC.Qt.AlignCenter, elided_text)
