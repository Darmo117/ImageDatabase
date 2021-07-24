"""PyQt5 port of the layouts/flowlayout example from Qt v4.x"""

import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtWidgets as QtW
from PyQt5.QtCore import Qt


class FlowLayout(QtW.QLayout):
    """Standard PyQt examples FlowLayout modified to work with a scrollable parent."""

    def __init__(self, parent: QtW.QWidget = None, margin: int = 0, spacing: int = -1):
        """Creates a flow layout.

        :param parent: An optional parent for this layout.
        :param margin: Margins value.
        :param spacing: Inner spacing value.
        """
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

        self._item_list: typ.List[QtW.QLayoutItem] = []

    @property
    def items(self) -> typ.List[QtW.QWidget]:
        """Returns a list of all inner widgets in the order they have been added."""
        return [item.widget() for item in self._item_list]

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QtC.QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtC.QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()
        size += QtC.QSize(2 * margin, 2 * margin)

        return size

    def clear(self):
        """Removes all inner components."""
        for i in reversed(range(self.count())):
            if self.itemAt(i).widget() is not None:
                # noinspection PyTypeChecker
                self.itemAt(i).widget().setParent(None)

    def _do_layout(self, rect: QtC.QRect, test_only: bool = False) -> int:
        """Sets the geometry of this layout and its inner widgets.

        :param rect: The rectangle of this layout.
        :param test_only: Used only in heightForWidth method.
        :return: The height of this layout.
        """
        x = rect.x()
        y = rect.y()
        line_height = 0

        for item in self._item_list:
            width = item.widget()
            space_x = self.spacing() + width.style().layoutSpacing(
                QtW.QSizePolicy.PushButton,
                QtW.QSizePolicy.PushButton,
                Qt.Horizontal
            )
            space_y = self.spacing() + width.style().layoutSpacing(
                QtW.QSizePolicy.PushButton,
                QtW.QSizePolicy.PushButton,
                Qt.Vertical
            )
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QtC.QRect(QtC.QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()

    def __del__(self):
        self.clear()


class ScrollingFlowWidget(QtW.QWidget):
    """A resizable and scrollable widget that uses a flow layout.
    Use its add_widget() method to flow children into it.
    """

    def __init__(self, parent: QtW.QWidget = None):
        super().__init__(parent)
        grid = QtW.QGridLayout(self)
        scroll = _ResizeScrollArea()
        self._wrapper = QtW.QWidget(scroll)
        self._flow_layout = FlowLayout(self._wrapper)
        self._wrapper.setLayout(self._flow_layout)
        scroll.setWidget(self._wrapper)
        scroll.setWidgetResizable(True)
        grid.addWidget(scroll)

    def add_widget(self, widget: QtW.QWidget):
        """Adds a widget to the underlying flow flayout.

        :param widget: The widget to add.
        """
        self._flow_layout.addWidget(widget)

    def clear_widgets(self):
        """Removes all widgets in the underlying flow layout."""
        self._flow_layout.clear()


class _ResizeScrollArea(QtW.QScrollArea):
    """A QScrollArea that propagates the resizing to any FlowLayout children."""

    def resizeEvent(self, event):
        wrapper = self.findChild(QtW.QWidget)
        flow = wrapper.findChild(FlowLayout)

        if wrapper and flow:
            width = self.viewport().width()
            height = flow.heightForWidth(width)
            size = QtC.QSize(width, height)
            point = self.viewport().rect().topLeft()
            flow.setGeometry(QtC.QRect(point, size))
            self.viewport().update()

        super().resizeEvent(event)
