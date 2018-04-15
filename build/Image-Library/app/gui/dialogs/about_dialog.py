from datetime import datetime

import PyQt5.QtWidgets as QtW

import config
from .dialog_base import Dialog


class AboutDialog(Dialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent, title="About", mode=Dialog.CLOSE)

    def _init_body(self):
        self.setFixedSize(220, 200)

        body = QtW.QHBoxLayout()

        label = QtW.QTextEdit()
        year = datetime.now().year
        label.setText("""
        <html style="color: black; font-size: 12px">
            <span style="font-size: 16px; font-weight: bold">Image Library v{}</span>
            <p>&copy; {} Damien Vergnet.</p>
            <p>Icons &copy; FatCow.</p>
        </html>
        """.format(config.VERSION, "2018" + ("" if year == 2018 else " - " + str(year))))
        label.setEnabled(False)
        body.addWidget(label)

        return body
