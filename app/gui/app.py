import os
import sys

import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW
from PyQt5.QtCore import QThread

import config
from app import utils
from app.data_access import ImageDao, TagsDao, write_playlist
from app.gui.dialogs import EditImageDialog, EditTagsDialog, AboutDialog
from app.model import Image, TagType
from app.queries import query_to_sympy
from .components import ImageList


# TODO liste latérale pour les tags (rangés par type)
class Application(QtW.QMainWindow):
    def __init__(self):
        super().__init__()

        self._dao = ImageDao(config.DATABASE)

        self._init_ui()
        utils.center(self)
        self.show()

    # noinspection PyUnresolvedReferences
    def _init_ui(self):
        self.setWindowTitle("Image Library v" + config.VERSION)
        self.setWindowIcon(QtG.QIcon("icons/app_icon.png"))
        self.setGeometry(0, 0, 800, 600)
        self.setMinimumSize(400, 200)

        self._init_menu()

        self.setCentralWidget(QtW.QWidget())

        self._list = ImageList(drop_action=self._add_images)
        self._list.selectionModel().selectionChanged.connect(self._list_selection_changed)
        self._list.model().rowsInserted.connect(self._list_changed)
        self._list.model().rowsRemoved.connect(self._list_changed)
        self._list.itemDoubleClicked.connect(lambda i: self._edit_images([i.image]))

        self._ok_btn = QtW.QPushButton("OK")
        self._ok_btn.clicked.connect(self._fetch_images)

        self._input_field = QtW.QLineEdit()
        self._input_field.setPlaceholderText("Search tags…")
        self._input_field.returnPressed.connect(self._fetch_images)

        h_box = QtW.QHBoxLayout()
        h_box.addWidget(self._input_field)
        h_box.addWidget(self._ok_btn)

        v_box = QtW.QVBoxLayout()
        v_box.addWidget(self._list)
        v_box.addLayout(h_box)

        self.centralWidget().setLayout(v_box)

        self._input_field.setFocus()

    # noinspection PyUnresolvedReferences
    def _init_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        add_file_item = QtW.QAction("Add &File…", self)
        add_file_item.setIcon(QtG.QIcon("icons/image_add.png"))
        add_file_item.setShortcut("Ctrl+F")
        add_file_item.triggered.connect(self._add_image)
        file_menu.addAction(add_file_item)

        add_directory_item = QtW.QAction("Add &Directory…", self)
        add_directory_item.setIcon(QtG.QIcon("icons/folder_image.png"))
        add_directory_item.setShortcut("Ctrl+D")
        add_directory_item.triggered.connect(self._add_directory)
        file_menu.addAction(add_directory_item)

        file_menu.addSeparator()

        self._export_item = QtW.QAction("E&xport As Playlist…", self)
        self._export_item.setShortcut("Ctrl+Shift+E")
        self._export_item.triggered.connect(self._export_images)
        self._export_item.setEnabled(False)
        file_menu.addAction(self._export_item)

        file_menu.addSeparator()

        exit_item = QtW.QAction("&Exit", self)
        exit_item.setIcon(QtG.QIcon("icons/door_open.png"))
        exit_item.setShortcut("Ctrl+Q")
        exit_item.triggered.connect(QtW.qApp.quit)
        file_menu.addAction(exit_item)

        edit_menu = menubar.addMenu("&Edit")

        edit_tags_item = QtW.QAction("Edit Tags…", self)
        edit_tags_item.setIcon(QtG.QIcon("icons/tag_edit.png"))
        edit_tags_item.setShortcut("Ctrl+T")
        edit_tags_item.triggered.connect(self._edit_tags)
        edit_menu.addAction(edit_tags_item)

        edit_menu.addSeparator()

        self._replace_image_item = QtW.QAction("&Replace Image…", self)
        self._replace_image_item.setShortcut("Ctrl+R")
        self._replace_image_item.triggered.connect(self._replace_image)
        self._replace_image_item.setEnabled(False)
        edit_menu.addAction(self._replace_image_item)

        self._edit_images_item = QtW.QAction("Edit Images…", self)
        self._edit_images_item.setIcon(QtG.QIcon("icons/image_edit.png"))
        self._edit_images_item.setShortcut("Ctrl+E")
        self._edit_images_item.triggered.connect(lambda: self._edit_images(self._list.selected_images()))
        self._edit_images_item.setEnabled(False)
        edit_menu.addAction(self._edit_images_item)

        self._delete_images_item = QtW.QAction("Delete Images", self)
        self._delete_images_item.setIcon(QtG.QIcon("icons/image_delete.png"))
        self._delete_images_item.setShortcut("Delete")
        self._delete_images_item.triggered.connect(self._delete_images)
        self._delete_images_item.setEnabled(False)
        edit_menu.addAction(self._delete_images_item)

        help_menu = menubar.addMenu("&Help")

        about_item = QtW.QAction("About", self)
        about_item.setIcon(QtG.QIcon("icons/information.png"))
        about_item.triggered.connect(lambda: AboutDialog(self).show())
        help_menu.addAction(about_item)

    def _center(self):
        qr = self.frameGeometry()
        cp = QtW.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _add_image(self):
        file = utils.open_image_chooser(self)
        if file != utils.REJECTED:
            self._add_images([file])

    def _add_directory(self):
        images = utils.open_directory_chooser(self)
        if images == utils.NO_IMAGES:
            utils.show_info("No images in this directory!", parent=self)
        elif images != utils.REJECTED:
            self._add_images(images)

    def _add_images(self, images):
        if len(images) > 0:
            images_to_add = [i for i in images if not self._dao.image_registered(i)]
            if len(images_to_add) == 0:
                text = "Image" + ("s" if len(images) > 1 else "") + " already registered!"
                utils.show_info(text, parent=self)
            else:
                dialog = EditImageDialog(self, show_skip=len(images_to_add) > 1, mode=EditImageDialog.ADD)
                dialog.set_on_close_action(self._fetch_images)
                dialog.set_images([Image(0, i) for i in images_to_add], {})
                dialog.show()

    def _replace_image(self):
        images = self._list.selected_images()
        if len(images) == 1:
            image = images[0]
            dialog = EditImageDialog(self, mode=EditImageDialog.REPLACE)
            dialog.set_on_close_action(self._fetch_images)
            tags = self._dao.get_image_tags(image.id)
            if tags is None:
                utils.show_error("Failed to load tags!")
            dialog.set_image(image, tags)
            dialog.show()

    def _export_images(self):
        images = self._list.get_images()
        if len(images) > 0:
            file = utils.open_playlist_saver(self)
            if file != utils.REJECTED:
                write_playlist(file, images)

    def _edit_images(self, images):
        if len(images) > 0:
            dialog = EditImageDialog(self, show_skip=len(images) > 1)
            dialog.set_on_close_action(self._fetch_images)
            tags = {}
            for image in images:
                t = self._dao.get_image_tags(image.id)
                if t is None:
                    utils.show_error("Failed to load tags!")
                tags[image.id] = t
            dialog.set_images(images, tags)
            dialog.show()

    def _delete_images(self):
        images = self._list.selected_images()

        if len(images) > 0:
            if len(images) > 1:
                message = "<html>Are you sure you want to delete these images?"
            else:
                message = "<html>Are you sure you want to delete this image?"
            message += "<br/><b>Files will be delete from the disk.</b></html>"
            choice = utils.show_question(message, "Delete", parent=self)
            if choice == QtW.QMessageBox.Yes:
                for item in images:
                    if self._dao.delete_image(item.id):
                        try:
                            os.remove(item.path)
                        except FileNotFoundError as e:
                            utils.show_error("Could not delete file!\n" + e.filename, parent=self)
                self._fetch_images()

    def _edit_tags(self):
        dialog = EditTagsDialog(self)
        dialog.show()

    class SearchThread(QThread):
        def __init__(self, tags, parent):
            super().__init__()
            self._tags = tags
            self._parent = parent
            self._images = []
            self._error = None

        def run(self):
            dao = ImageDao(config.DATABASE)
            expr = query_to_sympy(self._tags)
            if expr is None:
                self._error = "Syntax error!"
                return
            self._images = dao.get_images(expr)
            dao.close()
            if self._images is None:
                self._error = "Failed to load images!"

        @property
        def fetched_images(self):
            return self._images

        def failed(self):
            return self._error is not None

        @property
        def error(self):
            return self._error

    def _fetch_images(self):
        tags = self._input_field.text().strip()
        if len(tags) > 0:
            self._ok_btn.setEnabled(False)
            self._input_field.setEnabled(False)
            self._thread = Application.SearchThread(tags, self)
            # noinspection PyUnresolvedReferences
            self._thread.finished.connect(self._on_fetch_done)
            self._thread.start()

    def _on_fetch_done(self):
        if self._thread.failed():
            utils.show_error(self._thread.error, parent=self)
            self._ok_btn.setEnabled(True)
            self._input_field.setEnabled(True)
            return
        self._list.clear()
        images = self._thread.fetched_images
        images.sort(key=lambda i: i.path)
        for image in images:
            self._list.add_image(image)
        self._ok_btn.setEnabled(True)
        self._input_field.setEnabled(True)

    def _list_changed(self, _):
        self._export_item.setEnabled(self._list.count() > 0)

    def _list_selection_changed(self, selection):
        self._replace_image_item.setEnabled(len(selection) == 1)
        self._edit_images_item.setEnabled(len(selection) > 0)
        self._delete_images_item.setEnabled(len(selection) > 0)

    @staticmethod
    def _image_to_string(image):
        return image.path

    @classmethod
    def run(cls):
        app = QtW.QApplication(sys.argv)

        # Initialize tag types
        tags_dao = TagsDao(config.DATABASE)
        types = tags_dao.get_all_types()
        if types is None:
            utils.show_error("Could not load tag types! Shutting down.")
            sys.exit(-1)
        TagType.init(types)
        tags_dao.close()

        # noinspection PyUnusedLocal
        ex = cls()
        sys.exit(app.exec_())
