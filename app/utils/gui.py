import os
import typing as typ

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtW

from .. import constants, config
from ..i18n import translate as _t


def show_info(message: str, title='popup.info.title', parent: QtW.QWidget = None):
    """Shows an information popup.

    :param message: Popup’s message.
    :param title: Popup’s unlocalized title.
    :param parent: Popup’s parent.
    """
    mb = QtW.QMessageBox(QtW.QMessageBox.Information, _t(title), message, buttons=QtW.QMessageBox.Ok, parent=parent)
    mb.button(QtW.QMessageBox.Ok).setText(_t('dialog.common.ok_button.label'))
    mb.exec_()


def show_warning(message: str, title: str = 'popup.warning.title', parent: QtW.QWidget = None):
    """Shows a warning popup.

    :param message: Popup’s message.
    :param title: Popup’s unlocalized title.
    :param parent: Popup’s parent.
    """
    mb = QtW.QMessageBox(QtW.QMessageBox.Warning, _t(title), message, buttons=QtW.QMessageBox.Ok, parent=parent)
    mb.button(QtW.QMessageBox.Ok).setText(_t('dialog.common.ok_button.label'))
    mb.exec_()


def show_error(message: str, title: str = 'popup.error.title', parent: QtW.QWidget = None):
    """Shows an error popup.

    :param message: Popup’s message.
    :param title: Popup’s unlocalized title.
    :param parent: Popup’s parent.
    """
    mb = QtW.QMessageBox(QtW.QMessageBox.Critical, _t(title), message, buttons=QtW.QMessageBox.Ok, parent=parent)
    mb.button(QtW.QMessageBox.Ok).setText(_t('dialog.common.ok_button.label'))
    mb.exec_()


def show_question(message: str, title: str = 'popup.question.title', cancel: bool = False,
                  parent: QtW.QWidget = None) -> typ.Optional[bool]:
    """Shows a question popup.

    :param message: Popup’s message.
    :param title: Popup’s unlocalized title.
    :param cancel: If true a "Cancel" button will be added.
    :param parent: Popup’s parent.
    :return: True for yes, False for no or None for cancel.
    """
    answers = {
        QtW.QMessageBox.Yes: True,
        QtW.QMessageBox.No: False,
        QtW.QMessageBox.Cancel: None,
    }
    buttons = QtW.QMessageBox.Yes | QtW.QMessageBox.No
    if cancel:
        buttons |= QtW.QMessageBox.Cancel

    mb = QtW.QMessageBox(QtW.QMessageBox.Question, _t(title), message, buttons=buttons, parent=parent)
    mb.button(QtW.QMessageBox.Yes).setText(_t('dialog.common.yes_button.label'))
    mb.button(QtW.QMessageBox.No).setText(_t('dialog.common.no_button.label'))
    if cancel:
        mb.button(QtW.QMessageBox.Cancel).setText(_t('dialog.common.cancel_button.label'))
    # noinspection PyTypeChecker
    return answers[mb.exec_()]


def show_text_input(message: str, title: str, text: str = '', parent: QtW.QWidget = None) -> typ.Optional[str]:
    """Shows an input popup.

    :param message: Popup’s message.
    :param title: Popup’s title.
    :param text: Text to show in the input field.
    :param parent: Popup’s parent.
    :return: The typed text or None if the popup was cancelled.
    """
    input_d = QtW.QInputDialog(parent=parent)
    input_d.setWindowTitle(title)
    input_d.setLabelText(message)
    input_d.setTextValue(text)
    input_d.setOkButtonText(_t('dialog.common.ok_button.label'))
    input_d.setCancelButtonText(_t('dialog.common.cancel_button.label'))
    ok = input_d.exec_()
    return input_d.textValue() if ok else None


def show_int_input(message: str, title: str, value: int = 0, min_value: int = None, max_value: int = None,
                   parent: QtW.QWidget = None) -> typ.Optional[int]:
    """Shows an input popup.

    :param message: Popup’s message.
    :param title: Popup’s title.
    :param value: Value to show in the input field.
    :param min_value: Minimum value.
    :param max_value: Maximum value.
    :param parent: Popup’s parent.
    :return: The typed text or None if the popup was cancelled.
    """
    input_d = QtW.QInputDialog(parent=parent)
    input_d.setWindowTitle(title)
    input_d.setLabelText(message)
    input_d.setInputMode(QtW.QInputDialog.IntInput)
    if min_value is not None:
        input_d.setIntMinimum(min_value)
    if max_value is not None:
        input_d.setIntMaximum(max_value)
    input_d.setIntValue(value)
    input_d.setOkButtonText(_t('dialog.common.ok_button.label'))
    input_d.setCancelButtonText(_t('dialog.common.cancel_button.label'))
    ok = input_d.exec_()
    return input_d.intValue() if ok else None


def open_image_chooser(parent: QtW.QWidget = None) -> typ.Optional[typ.List[str]]:
    """Opens a file chooser for images.

    :param parent: Chooser’s parent.
    :return: The selected files or None if the chooser was cancelled.
    """
    exts = ' '.join(map(lambda e: '*.' + e, constants.FILE_EXTENSIONS))
    files, _ = QtW.QFileDialog.getOpenFileNames(
        caption=_t('popup.image_chooser.caption'),
        filter=_t('popup.image_chooser.filter') + f'({exts})',
        parent=parent,
        options=QtW.QFileDialog.DontUseNativeDialog if config.CONFIG.debug else None
    )
    return files or None


def open_playlist_saver(parent: typ.Optional[QtW.QWidget] = None) -> typ.Optional[str]:
    """Opens a file saver for playlists.

    :param parent: Saver’s parent.
    :return: The selected file or REJECTED if the saver was cancelled.
    """
    ext = '.play'
    file, _ = QtW.QFileDialog.getSaveFileName(
        caption=_t('popup.playlist_saver.caption'),
        filter=_t('popup.playlist_saver.filter') + f'(*{ext})',
        parent=parent,
        options=QtW.QFileDialog.DontUseNativeDialog if config.CONFIG.debug else None
    )
    if file and not file.endswith(ext):
        file += ext
    return file or None


def open_directory_chooser(parent: QtW.QWidget = None) -> typ.Optional[typ.List[str]]:
    """Opens a directory chooser then returns all the files it contains.

    :param parent: Chooser’s parent.
    :return: All files inside the chosen directory or REJECTED if the chooser was cancelled or NO_IMAGES if the
             directory contains no images.
    """
    directory = QtW.QFileDialog.getExistingDirectory(
        caption=_t('popup.open_directory_chooser.caption'),
        parent=parent,
        options=QtW.QFileDialog.DontUseNativeDialog if config.CONFIG.debug else None
    )
    if directory != '':
        files = filter(lambda f: os.path.splitext(f)[1].lower()[1:] in constants.FILE_EXTENSIONS, os.listdir(directory))
        files = list(map(lambda f: slashed(os.path.join(directory, f)), files))
        return files
    return None


def choose_directory(parent: QtW.QWidget = None) -> typ.Optional[str]:
    """Opens a directory chooser.

    :param parent: Chooser’s parent.
    :return: The selected directory or REJECTED if the chooser was cancelled.
    """
    directory = QtW.QFileDialog.getExistingDirectory(
        caption=_t('popup.directory_chooser.caption'),
        parent=parent,
        options=QtW.QFileDialog.DontUseNativeDialog if config.CONFIG.debug else None
    )
    return directory or None


def slashed(path: str) -> str:
    r"""Replaces backslashes (\) in the given path with normal slashes (/).

    :param path: The path to convert.
    :return: The path with all \ replaced by /.
    """
    return path.replace('\\', '/')


def center(window: QtW.QWidget):
    """Centers the given window on the screen.

    :param window: The window to center.
    """
    rect = window.frameGeometry()
    center = QtW.QDesktopWidget().availableGeometry().center()
    rect.moveCenter(center)
    window.move(rect.topLeft())


def negate(color: QtGui.QColor) -> QtGui.QColor:
    """Negates the given color.

    :param color: The base color.
    :return: The negated color.
    """
    return QtGui.QColor(255 - color.red(), 255 - color.green(), 255 - color.blue())
