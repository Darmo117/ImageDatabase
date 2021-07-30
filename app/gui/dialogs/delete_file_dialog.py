import PyQt5.QtWidgets as QtW

from app.i18n import translate as _t


class DeleteFileConfirmDialog(QtW.QMessageBox):
    """Message box thats asks the user if they want to delete some files."""

    def __init__(self, images_nb: int, parent: QtW.QWidget = None):
        """Creates a dialog.

        :param images_nb: Number of images that are pending deletion.
        :param parent: Parent widget.
        """
        if images_nb > 1:
            message = _t('popup.delete_image_warning.text_question_multiple')
        else:
            message = _t('popup.delete_image_warning.text_question_single')
        super().__init__(QtW.QMessageBox.Question, _t('popup.delete_image_warning.title'), message,
                         QtW.QMessageBox.Yes | QtW.QMessageBox.No, parent=parent)
        self.button(QtW.QMessageBox.Yes).setText(_t('dialog.common.yes_button.label'))
        self.button(QtW.QMessageBox.No).setText(_t('dialog.common.no_button.label'))
        # noinspection PyTypeChecker
        layout: QtW.QGridLayout = self.layout()
        self._delete_disk_chck = QtW.QCheckBox(_t('popup.delete_image_warning.checkbox_label'), parent=self)
        self._delete_disk_chck.setChecked(True)
        layout.addItem(QtW.QWidgetItem(self._delete_disk_chck), 1, 2)

    def delete_from_disk(self) -> bool:
        """Returns True if the file(s) have to be deleted from the disk; False otherwise."""
        return self._delete_disk_chck.isChecked()

    def exec_(self) -> int:
        button = super().exec_()
        return int(button == QtW.QMessageBox.Yes)
