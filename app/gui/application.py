import os
import re
import sys
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

import app.data_access as da
import app.model as model
import app.queries as queries
import app.utils as utils
import config
from app.logging import logger
from .components import ImageList, TagTree
from .dialogs import EditImageDialog, EditTagsDialog, AboutDialog


class Application(QtW.QMainWindow):
    """Application's main class."""

    def __init__(self):
        super().__init__()

        self._dao = da.ImageDao(config.DATABASE)
        self._tags_dao = da.TagsDao(config.DATABASE)

        self._init_ui()
        utils.center(self)

    # noinspection PyUnresolvedReferences
    def _init_ui(self):
        """Initializes the UI."""
        self.setWindowTitle("Image Library v" + config.VERSION)
        self.setWindowIcon(QtG.QIcon("app/icons/app_icon.png"))
        self.setGeometry(0, 0, 800, 600)
        self.setMinimumSize(400, 200)

        self._init_menu()

        self.setCentralWidget(QtW.QWidget())

        self._tag_tree = TagTree()
        self._tag_tree.itemDoubleClicked.connect(self._tree_item_clicked)
        self._refresh_tree()

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

        splitter = QtW.QSplitter()

        left_layout = QtW.QHBoxLayout()
        left_layout.addWidget(self._tag_tree)
        left_layout.setContentsMargins(5, 5, 0, 5)

        h_box = QtW.QHBoxLayout()
        h_box.addWidget(self._input_field)
        h_box.addWidget(self._ok_btn)

        v_box = QtW.QVBoxLayout()
        v_box.addWidget(self._list)
        v_box.addLayout(h_box)
        v_box.setContentsMargins(0, 5, 5, 5)

        left = QtW.QWidget()
        left.setLayout(left_layout)
        right = QtW.QWidget()
        right.setLayout(v_box)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([100, 500])

        self.setCentralWidget(splitter)

        self._input_field.setFocus()

    # noinspection PyUnresolvedReferences
    def _init_menu(self):
        """Initializes the menu bar."""
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
        """Centers the application window."""
        qr = self.frameGeometry()
        cp = QtW.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _add_image(self):
        """Opens a file chooser then add the selected image to the database."""
        file = utils.open_image_chooser(self)
        if file != utils.REJECTED:
            self._add_images([file])

    def _add_directory(self):
        """Opens a file chooser then add the images from the selected directory to the database."""
        images = utils.open_directory_chooser(self)
        if images == utils.NO_IMAGES:
            utils.show_info("No images in this directory!", parent=self)
        elif images != utils.REJECTED:
            self._add_images(images)

    def _add_images(self, images: typ.List[str]):
        """Opens the 'Add Images' dialog then adds the images to the database. Checks for duplicates."""
        if len(images) > 0:
            images_to_add = [i for i in images if not self._dao.image_registered(i)]
            if len(images_to_add) == 0:
                plural = "s" if len(images) > 1 else ""
                text = f"Image{plural} already registered!"
                utils.show_info(text, parent=self)
            else:
                dialog = EditImageDialog(self, show_skip=len(images_to_add) > 1, mode=EditImageDialog.ADD)
                dialog.set_on_close_action(self._fetch_and_refresh)
                dialog.set_images([model.Image(0, i) for i in images_to_add], {})
                dialog.show()

    def _replace_image(self):
        """Opens the 'Replace Image' dialog then replaces the image with the selected one."""
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
        """Opens a file saver then writes all images to a playlist file."""
        images = self._list.get_images()
        if len(images) > 0:
            file = utils.open_playlist_saver(self)
            if file != utils.REJECTED:
                da.write_playlist(file, images)
        utils.show_info("Exported playlist!", parent=self)

    def _fetch_and_refresh(self):
        """Fetches images then refreshes the list."""
        self._fetch_images()
        self._refresh_tree()

    def _edit_images(self, images: typ.List[model.Image]):
        """Opens the 'Edit Images' dialog then updates all edited images."""
        if len(images) > 0:
            dialog = EditImageDialog(self, show_skip=len(images) > 1)
            dialog.set_on_close_action(self._fetch_and_refresh)
            tags = {}
            for image in images:
                t = self._dao.get_image_tags(image.id)
                if t is None:
                    utils.show_error("Failed to load tags!")
                tags[image.id] = t
            dialog.set_images(images, tags)
            dialog.show()

    def _delete_images(self):
        """Deletes the selected images. User is asked to confirm the action."""
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
                            logger.exception(e)
                            utils.show_error("Could not delete file!\n" + e.filename, parent=self)
                self._fetch_images()

    def _edit_tags(self):
        """Opens the 'Edit Tags' dialog. Tags tree is refreshed afterwards."""
        dialog = EditTagsDialog(self)
        dialog.set_on_close_action(self._refresh_tree)
        dialog.show()

    def _tree_item_clicked(self, item: QtW.QTreeWidgetItem):
        """
        Called when a item in the tags tree is clicked.

        :param item: The clicked item.
        """
        if item.whatsThis(0) == "tag":
            self._input_field.setText((self._input_field.text() + " " + item.text(0)).lstrip())

    def _refresh_tree(self):
        """Refreshes the tags tree."""
        self._tag_tree.refresh(model.TagType.SYMBOL_TYPES.values(), self._tags_dao.get_all_tags())

    class _SearchThread(QtC.QThread):
        """This thread is used to search images from a query."""

        _MAXIMUM_DEPTH = 20

        def __init__(self, query: str):
            """
            Creates a search thread for a query.

            :param query: The query.
            """
            super().__init__()
            self._query = query
            self._images = []
            self._error = None

        def run(self):
            images_dao = da.ImageDao(config.DATABASE)
            tags_dao = da.TagsDao(config.DATABASE)
            compound_tags: typ.List[model.CompoundTag] = tags_dao.get_all_tags(tag_class=model.CompoundTag)
            previous_query = ""
            depth = 0
            # Replace compound tags until none are present
            while self._query != previous_query:
                for tag in compound_tags:
                    previous_query = self._query
                    self._query = re.sub(f"(\W|^){tag.label}(\W|$)", fr"\1({tag.definition})\2", self._query)
                depth += 1
                if depth >= self._MAXIMUM_DEPTH:
                    self._error = f"Maximum recursion depth of {self._MAXIMUM_DEPTH} reached!"
                    return
            try:
                print(self._query)  # DEBUG
                expr = queries.query_to_sympy(self._query, simplify=False)  # TEMP
            except ValueError as e:
                self._error = str(e)
                return
            self._images = images_dao.get_images(expr)
            images_dao.close()
            if self._images is None:
                self._error = "Failed to load images!"

        @property
        def fetched_images(self) -> typ.List[model.Image]:
            """Returns all fetched images."""
            return self._images

        def failed(self) -> bool:
            """Returns true if the operation failed."""
            return self._error is not None

        @property
        def error(self) -> typ.Optional[str]:
            """If the operation failed, returns the reason; otherwise returns None."""
            return self._error

    def _fetch_images(self):
        """Fetches images matching the typed query. Starts a search thread to avoid freezing the whole application."""
        tags = self._input_field.text().strip()
        if len(tags) > 0:
            self._ok_btn.setEnabled(False)
            self._input_field.setEnabled(False)
            self._thread = self._SearchThread(tags)
            # noinspection PyUnresolvedReferences
            self._thread.finished.connect(self._on_fetch_done)
            self._thread.start()

    def _on_fetch_done(self):
        """Called when images searching is done."""
        if self._thread.failed():
            utils.show_error(self._thread.error, parent=self)
            self._ok_btn.setEnabled(True)
            self._input_field.setEnabled(True)
        else:
            self._list.clear()
            images = self._thread.fetched_images
            images.sort(key=lambda i: i.path)
            for image in images:
                self._list.add_image(image)
            self._ok_btn.setEnabled(True)
            self._input_field.setEnabled(True)
            self._input_field.setFocus()

    def _list_changed(self, _):
        """Called when images list content changes."""
        self._export_item.setEnabled(self._list.count() > 0)

    def _list_selection_changed(self, selection: list):
        """
        Called when the selection in images list changes.

        :param selection: The current selection.
        """
        self._replace_image_item.setEnabled(len(selection) == 1)
        self._edit_images_item.setEnabled(len(selection) > 0)
        self._delete_images_item.setEnabled(len(selection) > 0)

    @classmethod
    def run(cls):
        """Run an instance of this Application class."""
        try:
            app = QtW.QApplication(sys.argv)

            da.update_if_needed()

            # Initialize tag types
            tags_dao = da.TagsDao(config.DATABASE)
            types = tags_dao.get_all_types()
            if types is None:
                utils.show_error("Could not load data! Shutting down.")
                sys.exit(1)
            model.TagType.init(types)
            tags_dao.close()

            cls().show()
        except BaseException as e:
            logger.exception(e)
        else:
            sys.exit(app.exec_())
