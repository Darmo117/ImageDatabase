import os
import typing as typ

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtW
from PyQt5.QtCore import Qt

from . import constants
from .i18n import translate as _t


def show_info(message: str, title='popup.info.title', parent: QtW.QWidget = None):
    """Shows an information popup.

    :param message: Popup’s message.
    :param title: Popup’s unlocalized title.
    :param parent: Popup’s parent.
    """
    QtW.QMessageBox.information(parent, _t(title), message)


def show_warning(message: str, title: str = 'popup.warning.title', parent: QtW.QWidget = None):
    """Shows a warning popup.

    :param message: Popup’s message.
    :param title: Popup’s unlocalized title.
    :param parent: Popup’s parent.
    """
    QtW.QMessageBox.warning(parent, _t(title), message)


def show_error(message: str, title: str = 'popup.error.title', parent: QtW.QWidget = None):
    """Shows an error popup.

    :param message: Popup’s message.
    :param title: Popup’s unlocalized title.
    :param parent: Popup’s parent.
    """
    QtW.QMessageBox.critical(parent, _t(title), message)


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
        QtW.QMessageBox.Cancel: None
    }
    mode = QtW.QMessageBox.Yes | QtW.QMessageBox.No
    if cancel:
        mode |= QtW.QMessageBox.Cancel
    return answers[QtW.QMessageBox.question(parent, _t(title), message, mode)]


def show_text_input(message: str, title: str, text: str = '', parent: QtW.QWidget = None) -> typ.Optional[str]:
    """Shows an input popup.

    :param message: Popup’s message.
    :param title: Popup’s title.
    :param text: Text to show in the input field.
    :param parent: Popup’s parent.
    :return: The typed text or None if the popup was cancelled.
    """
    text, ok = QtW.QInputDialog.getText(parent, title, message, text=text, flags=Qt.WindowCloseButtonHint)
    return text if ok else None


def show_int_input(message: str, title: str, value: int = 0, min_value: int = -2147483647, max_value: int = 2147483647,
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
    # noinspection PyArgumentList
    value, ok = QtW.QInputDialog.getInt(parent, title, message, value=value, min=min_value, max=max_value,
                                        flags=Qt.WindowCloseButtonHint)
    return value if ok else None


def open_image_chooser(parent: QtW.QWidget = None) -> typ.Optional[str]:
    """Opens a file chooser for images.

    :param parent: Chooser’s parent.
    :return: The selected file or REJECTED if the chooser was cancelled.
    """
    exts = ' '.join(map(lambda e: '*.' + e, constants.FILE_EXTENSIONS))
    print(_t('popup.image_chooser.filter', extensions=exts))
    file, _ = QtW.QFileDialog.getOpenFileName(
        caption=_t('popup.image_chooser.caption'),
        filter=_t('popup.image_chooser.filter') + f'({exts})',
        parent=parent
    )
    return file or None


def open_playlist_saver(parent: typ.Optional[QtW.QWidget] = None) -> typ.Optional[str]:
    """Opens a file saver for playlists.

    :param parent: Saver’s parent.
    :return: The selected file or REJECTED if the saver was cancelled.
    """
    ext = '.play'
    file, _ = QtW.QFileDialog.getSaveFileName(
        caption=_t('popup.playlist_saver.caption'),
        filter=_t('popup.playlist_saver.filter') + f'(*{ext})',
        parent=parent
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
    directory = QtW.QFileDialog.getExistingDirectory(caption=_t('popup.open_directory_chooser.caption'), parent=parent)
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
    directory = QtW.QFileDialog.getExistingDirectory(caption=_t('popup.directory_chooser.caption'), parent=parent)
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
