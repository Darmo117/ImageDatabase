import typing as typ
from datetime import datetime

import PyQt5.QtWidgets as QtW

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
        self.setMinimumSize(280, 170)

        body = QtW.QHBoxLayout()

        label = QtW.QLabel(parent=self)
        year = datetime.now().year
        copyright_year = '' if year == 2018 else ' - ' + str(year)
        label.setText(f"""
        <html style="font-size: 12px">
            <span style="font-size: 16px; font-weight: bold">Image Library v{constants.VERSION}</span>
            <p>© 2018{copyright_year} Damien Vergnet</p>
            <p>Icons © FatCow</p>
            <p>Find more on <a href="https://github.com/Darmo117/ImageDatabase">GitHub</a>.</p>
        </html>
        """)
        label.setOpenExternalLinks(True)
        body.addWidget(label)

        return body
