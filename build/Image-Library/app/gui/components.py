import os

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

from app import utils
import config


class ImageItem(QtW.QListWidgetItem):
    def __init__(self, parent, image):
        super().__init__(parent=parent)
        self.setText(image.path)
        self._image = image

    @property
    def image(self):
        return self._image


class ImageList(QtW.QListWidget):
    def __init__(self, parent=None, drop_action=None):
        super().__init__(parent)
        self.setSelectionMode(QtW.QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        self._drop_action = drop_action

    def add_image(self, image):
        self.addItem(ImageItem(self, image))

    def get_images(self):
        # noinspection PyUnresolvedReferences
        return [self.item(i).image for i in range(self.count())]

    def selected_images(self):
        # noinspection PyUnresolvedReferences
        return [self.item(i.row()).image for i in self.selectedIndexes()]

    def dragEnterEvent(self, event):
        ImageList._check_drag(event)

    def dragMoveEvent(self, event):
        ImageList._check_drag(event)

    def dropEvent(self, event):
        if self._drop_action is not None:
            self._drop_action(ImageList._get_urls(event))

    @staticmethod
    def _check_drag(event):
        if event.mimeData().hasUrls():
            try:
                urls = ImageList._get_urls(event)
            except ValueError:
                event.ignore()
            else:
                if all(map(lambda f: os.path.splitext(f)[1].lower()[1:] in config.EXTENSIONS, urls)):
                    event.accept()
                else:
                    event.ignore()
        else:
            event.ignore()

    @staticmethod
    def _get_urls(event):
        urls = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                raise ValueError("URL is not local")
            urls.append(url.toLocalFile())
        return urls


class Canvas(QtW.QGraphicsView):
    def __init__(self):
        super().__init__()
        self._image = None

    def set_image(self, image_path):
        self.setScene(QtW.QGraphicsScene())
        if os.path.exists(image_path):
            self._image = QtG.QPixmap(image_path)
            self.scene().addPixmap(self._image)
            self.fit()
        else:
            utils.show_error("Could not load image!", parent=self)
            self._image = None
            self.scene().addText("No image")

    def fit(self):
        if self._image is not None and not self.rect().contains(self._image.rect()):
            self.fitInView(self.scene().sceneRect(), QtC.Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        self.fit()
        return super().resizeEvent(event)


class EllipsisLabel(QtW.QLabel):
    def paintEvent(self, event):
        painter = QtG.QPainter()
        painter.begin(self)
        self.draw_text(event, painter)
        painter.end()

    def draw_text(self, event, painter):
        metrics = QtG.QFontMetrics(self.font())
        elided_text = metrics.elidedText(self.text(), QtC.Qt.ElideRight, self.width())
        painter.drawText(event.rect(), QtC.Qt.AlignCenter, elided_text)
