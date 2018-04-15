import PyQt5.QtWidgets as QtW
from PyQt5.QtCore import Qt

import app.utils as utils


class Dialog(QtW.QDialog):
    OK_CANCEL = 0
    CLOSE = 1

    def __init__(self, parent=None, title=None, modal=True, mode=OK_CANCEL):
        # Remove "?" button but keep "close" button.
        super().__init__(parent)
        # noinspection PyTypeChecker
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(modal)

        self._buttons_mode = mode

        if self._buttons_mode != Dialog.OK_CANCEL and self._buttons_mode != Dialog.CLOSE:
            raise ValueError("Unknown mode " + str(self._buttons_mode))

        self._close_action = None
        # noinspection PyUnresolvedReferences
        self.rejected.connect(self.close)

        if title:
            self.setWindowTitle(title)

        body = QtW.QVBoxLayout()
        center = self._init_body()
        if center is not None:
            # noinspection PyTypeChecker
            body.addLayout(center)
        body.addLayout(self.__init_button_box())

        self.setLayout(body)
        utils.center(self)

    def _init_body(self) -> QtW.QLayout or None:
        return None

    # noinspection PyUnresolvedReferences
    def __init_button_box(self):
        box = QtW.QHBoxLayout()
        box.addStretch(1)

        self._ok_btn = QtW.QPushButton("OK" if self._buttons_mode == Dialog.OK_CANCEL else "Close")
        self._ok_btn.clicked.connect(self._on_ok_clicked)
        self._cancel_btn = QtW.QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)

        buttons = self._init_buttons()
        for b in buttons:
            box.addWidget(b)

        box.addWidget(self._ok_btn)
        if self._buttons_mode == Dialog.OK_CANCEL:
            box.addWidget(self._cancel_btn)

        return box

    def _init_buttons(self) -> list:
        return []

    def set_on_close_action(self, action):
        self._close_action = action

    def _on_ok_clicked(self):
        if self._buttons_mode == Dialog.CLOSE:
            self.close()
        else:
            if not self._is_valid():
                utils.show_error("Invalid data!", parent=self)
            elif self._apply():
                self.close()

    def _is_valid(self) -> bool:
        return True

    def _apply(self) -> bool:
        return True

    def closeEvent(self, event):
        if self._close_action is not None:
            self._close_action()
