import typing as typ
from datetime import datetime

import PyQt5.QtCore as QtC
import PyQt5.QtWidgets as QtW
import pyperclip

from app import constants
from app.i18n import translate as _t
from . import _dialog_base


class AboutDialog(_dialog_base.Dialog):
    """This dialog shows information about the application."""

    def __init__(self, parent: typ.Optional[QtW.QWidget] = None):
        """Creates the 'About' dialog.

        :param parent: The widget this dialog is attached to.
        """
        super().__init__(parent=parent,
                         title=_t('dialog.about.title', app_name=constants.APP_NAME),
                         modal=True,
                         mode=_dialog_base.Dialog.CLOSE)

    def _init_body(self) -> QtW.QLayout:
        self.setMinimumSize(200, 140)

        body = QtW.QHBoxLayout()

        self._label = QtW.QLabel(parent=self)
        year = datetime.now().year
        copyright_year = '' if year == 2018 else f' - {year}'
        self._label.setText(f"""
        <html style="font-size: 12px">
            <h1>Image Library v{constants.VERSION}</h1>
            <p>© 2018{copyright_year} Damien Vergnet</p>
            <p>Icons © FatCow</p>
            <p>Find more on <a href="https://github.com/Darmo117/ImageDatabase">GitHub</a>.</p>
        </html>
        """.strip())
        self._label.setOpenExternalLinks(True)
        self._label.setContextMenuPolicy(QtC.Qt.CustomContextMenu)
        self._label.customContextMenuRequested.connect(self._link_context_menu)
        self._label.linkHovered.connect(self._update_current_link)
        body.addWidget(self._label)
        self._current_link = None

        self._label_menu = QtW.QMenu(parent=self._label)
        self._label_menu.addAction(_t('dialog.about.menu.copy_link_item'))
        self._label_menu.triggered.connect(lambda: pyperclip.copy(self._current_link))

        return body

    def _update_current_link(self, url: str):
        self._current_link = url

    def _link_context_menu(self, pos: QtC.QPoint):
        if self._current_link:
            self._label_menu.exec_(self._label.mapToGlobal(pos))
