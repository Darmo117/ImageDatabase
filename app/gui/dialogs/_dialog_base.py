from __future__ import annotations

import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

from app import utils
from app.i18n import translate as _t

_T = typ.TypeVar('_T', bound='Dialog')


class Dialog(QtW.QDialog):
    """Base class for all dialog windows."""
    OK_CANCEL = 0
    CLOSE = 1

    def __init__(self, parent: typ.Optional[QtW.QWidget] = None, title: typ.Optional[str] = None, modal: bool = True,
                 mode: int = OK_CANCEL):
        """Creates a dialog window.

        :param parent: The widget this dialog is attached to.
        :param title: Dialog’s title.
        :param modal: If true all events to the parent widget will be blocked while this dialog is visible.
        :param mode: Buttons mode. OK_CANCEL will add 'OK' and 'Cancel' buttons; CLOSE will add a single 'Close' button.
        """
        super().__init__(parent)
        # Remove "?" button but keep "close" button.
        # noinspection PyTypeChecker
        self.setWindowFlags(self.windowFlags() & ~QtC.Qt.WindowContextHelpButtonHint)
        self.setModal(modal)
        if modal:
            self.setAttribute(QtC.Qt.WA_DeleteOnClose)

        self._buttons_mode = mode

        if self._buttons_mode != Dialog.OK_CANCEL and self._buttons_mode != Dialog.CLOSE:
            raise ValueError(f'unknown mode "{self._buttons_mode}"')

        self._close_action = None
        self._applied = False
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
        utils.gui.center(self)

    def _init_body(self) -> typ.Optional[QtW.QLayout]:
        """Initializes this dialog’s body.

        :return: The components to disply in this dialog.
        """
        return None

    def __init_button_box(self) -> QtW.QBoxLayout:
        """Initializes the buttons. Additional buttons can be set by overriding the _init_buttons method. These buttons
        will be added in the order they are returned and to the left of default buttons.

        :return: The list of buttons.
        """
        box = QtW.QHBoxLayout()
        box.addStretch(1)

        self._ok_btn = QtW.QPushButton(
            self.style().standardIcon(QtW.QStyle.SP_DialogOkButton),
            _t('dialog.common.ok_button.label') if self._buttons_mode == Dialog.OK_CANCEL
            else _t('dialog.common.close_button.label'),
            parent=self
        )
        self._ok_btn.clicked.connect(self._on_ok_clicked)
        if self._buttons_mode == Dialog.OK_CANCEL:
            self._cancel_btn = QtW.QPushButton(
                self.style().standardIcon(QtW.QStyle.SP_DialogCancelButton),
                _t('dialog.common.cancel_button.label'),
                parent=self
            )
            self._cancel_btn.clicked.connect(self.reject)

        buttons = self._init_buttons()
        for b in buttons:
            box.addWidget(b)

        box.addWidget(self._ok_btn)
        if self._buttons_mode == Dialog.OK_CANCEL:
            box.addWidget(self._cancel_btn)

        return box

    def _init_buttons(self) -> typ.List[QtW.QAbstractButton]:
        """Use this method to return additional buttons.

        :return: The list of additional buttons.
        """
        return []

    def set_on_close_action(self, action: typ.Callable[[_T], None]):
        """Sets the action that will be called when this dialog closes after the user clicked OK/Apply.

        :param action: The action to call when this dialog closes.
            The dialog instance will be passed as the single argument.
        """
        self._close_action = action

    def _on_ok_clicked(self):
        """Called when the OK button is clicked. Checks the validity of this dialog and applies changes if possible."""
        if self._buttons_mode == Dialog.CLOSE:
            self.close()
        else:
            if not self._is_valid():
                reason = self._get_error()
                utils.gui.show_error(
                    reason if reason is not None else _t('dialog.common.invalid_data.text'),
                    parent=self
                )
            elif self._apply():
                self.close()

    def _is_valid(self) -> bool:
        """Checks if this dialog’s state is valid. Called when the dialog closes. An invalid state will prevent the
        dialog from closing.

        :return: True if everything is fine; false otherwise.
        """
        return True

    def _get_error(self) -> typ.Optional[str]:
        """Returns the reason data is invalid. If data is valid, None is returned."""
        return None

    def _apply(self) -> bool:
        """Applies changes. Called when the dialog closes and is in a valid state.

        :return: True if the changes were applied.
        """
        self._applied = True
        return True

    def closeEvent(self, event: QtG.QCloseEvent):
        if self._close_action is not None and self._applied:
            self._close_action(self)
