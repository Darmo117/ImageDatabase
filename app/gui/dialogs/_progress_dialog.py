import PyQt5.QtWidgets as QtW

from app.i18n import translate as _t


class ProgressDialog(QtW.QProgressDialog):
    def __init__(self, parent: QtW.QWidget = None):
        super().__init__('', _t('dialog.common.cancel_button.label'), 0, 100, parent=parent)
        self.setWindowTitle(_t('popup.progress.title'))
        self.setMinimumDuration(500)
        self.setModal(parent is not None)
