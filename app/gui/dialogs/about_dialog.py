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
        self.setFixedSize(220, 200)

        body = QtW.QHBoxLayout()

        label = QtW.QTextEdit()
        year = datetime.now().year
        copyright_year = "" if year == 2018 else " - " + str(year)
        label.setText(f"""
        <html style="color: black; font-size: 12px">
            <span style="font-size: 16px; font-weight: bold">Image Library v{config.VERSION}</span>
            <p>&copy; 2018{copyright_year} Damien Vergnet.</p>
            <p>Icons &copy; FatCow.</p>
        </html>
        """)
        label.setEnabled(False)
        body.addWidget(label)

        return body
