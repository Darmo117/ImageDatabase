import os
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

import app.model as model
import app.utils as utils


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

    def __init__(self, show_errors: bool = True):
        """
        Creates an empty canvas with no image.

        :param show_errors: If true a popup will appear when an image cannot be loaded.
        """
        super().__init__()
        self._image = None
        self._show_errors = show_errors

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
            if self._show_errors:
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
