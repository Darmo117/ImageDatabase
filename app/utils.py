import os

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDesktopWidget

import config


def show_info(message, title="Information", parent=None):
    QMessageBox.information(parent, title, message)


def show_warning(message, title="Warning", parent=None):
    QMessageBox.warning(parent, title, message)


def show_error(message, title="Error", parent=None):
    QMessageBox.critical(parent, title, message)


def show_question(message, title="Question", cancel=False, parent=None):
    mode = QMessageBox.Yes | QMessageBox.No
    if cancel:
        mode |= QMessageBox.Cancel
    return QMessageBox.question(parent, title, message, mode)


REJECTED = 1


def open_image_chooser(parent=None):
    exts = "; ".join(map(lambda e: "*." + e, config.FILE_EXTENSIONS))
    file, _ = QFileDialog.getOpenFileName(caption="Open Image", filter="Image file (" + exts + ")", parent=parent)
    return file if file != "" else REJECTED


def open_playlist_saver(parent=None):
    ext = ".play"
    file, _ = QFileDialog.getSaveFileName(caption="Save Playlist", filter="Playlist (*" + ext + ")", parent=parent)
    if file != "" and not file.endswith(ext):
        file += ext
    return file if file != "" else REJECTED


NO_IMAGES = 2


def open_directory_chooser(parent=None):
    directory = QFileDialog.getExistingDirectory(caption="Open Directory", parent=parent)
    if directory != "":
        files = filter(lambda f: os.path.splitext(f)[1].lower()[1:] in config.FILE_EXTENSIONS, os.listdir(directory))
        files = list(map(lambda f: slashed(os.path.join(directory, f)), files))
        return files if len(files) > 0 else NO_IMAGES
    return REJECTED


def choose_directory(parent=None):
    directory = QFileDialog.getExistingDirectory(caption="Choose Directory", parent=parent)
    return directory if directory != "" else REJECTED


def slashed(path):
    return path.replace("\\", "/")


def center(window):
    rect = window.frameGeometry()
    center = QDesktopWidget().availableGeometry().center()
    rect.moveCenter(center)
    window.move(rect.topLeft())


def negate(color: QColor):
    return QColor(255 - color.red(), 255 - color.green(), 255 - color.blue())


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    # show_info("Info")
    # show_warning("Hey!")
    # show_error("Oh no!")
    # show_question("???", cancel=True)
    app.exec_()
