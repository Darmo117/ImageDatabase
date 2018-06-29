import os
import typing as typ

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtW

import config


def show_info(message: str, title="Information", parent: QtW.QWidget = None):
    """
    Show an information popup.

    :param message: Popup's message.
    :param title: Popup's title.
    :param parent: Popup's parent.
    """
    QtW.QMessageBox.information(parent, title, message)


def show_warning(message: str, title: str = "Warning", parent: QtW.QWidget = None):
    """
    Show a warning popup.

    :param message: Popup's message.
    :param title: Popup's title.
    :param parent: Popup's parent.
    """
    QtW.QMessageBox.warning(parent, title, message)


def show_error(message: str, title: str = "Error", parent: QtW.QWidget = None):
    """
    Show an error popup.

    :param message: Popup's message.
    :param title: Popup's title.
    :param parent: Popup's parent.
    """
    QtW.QMessageBox.critical(parent, title, message)


def show_question(message: str, title: str = "Question", cancel: bool = False, parent: QtW.QWidget = None) \
        -> QtW.QMessageBox.StandardButton:
    """
    Show an question popup.

    :param message: Popup's message.
    :param title: Popup's title.
    :param cancel: If true a "Cancel" button will be added.
    :param parent: Popup's parent.
    :return: The clicked button.
    """
    mode = QtW.QMessageBox.Yes | QtW.QMessageBox.No
    if cancel:
        mode |= QtW.QMessageBox.Cancel
    return QtW.QMessageBox.question(parent, title, message, mode)


REJECTED = 1


def open_image_chooser(parent: QtW.QWidget = None) -> typ.Union[str, int]:
    """
    Opens a file chooser for images.

    :param parent: Chooser's parent.
    :return: The selected file or REJECTED if the chooser was cancelled.
    """
    exts = "; ".join(map(lambda e: "*." + e, config.FILE_EXTENSIONS))
    file, _ = QtW.QFileDialog.getOpenFileName(caption="Open Image", filter=f"Image file ({exts})", parent=parent)
    return file if file != "" else REJECTED


def open_playlist_saver(parent: typ.Optional[QtW.QWidget] = None) -> typ.Union[str, int]:
    """
    Opens a file saver for playlists.

    :param parent: Saver's parent.
    :return: The selected file or REJECTED if the saver was cancelled.
    """
    ext = ".play"
    file, _ = QtW.QFileDialog.getSaveFileName(caption="Save Playlist", filter=f"Playlist (*{ext})", parent=parent)
    if file != "" and not file.endswith(ext):
        file += ext
    return file if file != "" else REJECTED


NO_IMAGES = 2


def open_directory_chooser(parent: QtW.QWidget = None) -> typ.Union[typ.List[str], int]:
    """
    Opens a directory chooser then returns all the files it contains.

    :param parent: Chooser's parent.
    :return: All files inside the chosen directory or REJECTED if the chooser was cancelled or NO_IMAGES if the
             directory contains no images.
    """
    directory = QtW.QFileDialog.getExistingDirectory(caption="Open Directory", parent=parent)
    if directory != "":
        files = filter(lambda f: os.path.splitext(f)[1].lower()[1:] in config.FILE_EXTENSIONS, os.listdir(directory))
        files = list(map(lambda f: slashed(os.path.join(directory, f)), files))
        return files if len(files) > 0 else NO_IMAGES
    return REJECTED


def choose_directory(parent: QtW.QWidget = None) -> typ.Union[str, int]:
    """
    Opens a directory chooser.

    :param parent: Chooser's parent.
    :return: The selected directory or REJECTED if the chooser was cancelled.
    """
    directory = QtW.QFileDialog.getExistingDirectory(caption="Choose Directory", parent=parent)
    return directory if directory != "" else REJECTED


def slashed(path: str) -> str:
    """
    Replaces backslashes (\) in the given path with normal slashes (/).

    :param path: The path to convert.
    :return: The path with all \ replaced by /.
    """
    return path.replace("\\", "/")


def center(window: QtW.QWidget):
    """
    Centers the given window on the screen.

    :param window: The window to center.
    """
    rect = window.frameGeometry()
    center = QtW.QDesktopWidget().availableGeometry().center()
    rect.moveCenter(center)
    window.move(rect.topLeft())


def negate(color: QtGui.QColor) -> QtGui.QColor:
    """
    Negates the given color.

    :param color: The base color.
    :return: The negated color.
    """
    return QtGui.QColor(255 - color.red(), 255 - color.green(), 255 - color.blue())


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    # show_info("Info")
    # show_warning("Hey!")
    # show_error("Oh no!")
    # show_question("???", cancel=True)
    app.exec_()
