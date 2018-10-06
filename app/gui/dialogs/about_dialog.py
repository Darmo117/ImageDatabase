import typing as typ
from datetime import datetime

import PyQt5.QtWidgets as QtW

import config
from .dialog_base import Dialog


class AboutDialog(Dialog):
    """This dialog shows information about the application."""

    def __init__(self, parent: typ.Optional[QtW.QWidget] = None):
        """
        Creates an 'About' dialog.

        :param parent: The widget this dialog is attached to.
        """
        super().__init__(parent=parent, title="About", mode=Dialog.CLOSE)

    def _init_body(self) -> QtW.QLayout:
        self.setFixedSize(220, 170)

        body = QtW.QHBoxLayout()

        label = QtW.QLabel()
        year = datetime.now().year
        copyright_year = "" if year == 2018 else " - " + str(year)
        label.setText(f"""
        <html style="color: black; font-size: 12px">
            <span style="font-size: 16px; font-weight: bold">Image Library v{config.VERSION}</span>
            <p>© 2018{copyright_year} Damien Vergnet</p>
            <p>Icons © FatCow</p>
            <p>Find more on <a href="https://github.com/Darmo117">GitHub</a>.</p>
        </html>
        """)
        label.setOpenExternalLinks(True)
        body.addWidget(label)

        return body
