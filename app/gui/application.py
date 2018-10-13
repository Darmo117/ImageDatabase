import ctypes
import os
import re
import sys
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

from .components import TagTree
from .dialogs import EditImageDialog, EditTagsDialog, AboutDialog
from .image_list import ImageList, ImageListView, ThumbnailList
from .. import config, constants, data_access as da, model, queries, utils
from ..logging import logger


class Application(QtW.QMainWindow):
    """Application's main class."""

    def __init__(self):
        super().__init__()

        self._dao = da.ImageDao(config.CONFIG.database_path)
        self._tags_dao = da.TagsDao(config.CONFIG.database_path)

        self._init_ui()
        utils.center(self)

    # noinspection PyUnresolvedReferences
    def _init_ui(self):
        """Initializes the UI."""
        self.setWindowTitle("Image Library v" + constants.VERSION)
        self.setWindowIcon(QtG.QIcon("app/icons/app_icon.png"))
        self.setGeometry(0, 0, 800, 600)
        self.setMinimumSize(400, 200)

        self._init_menu()

        self.setCentralWidget(QtW.QWidget())

        self._tag_tree = TagTree()
        self._tag_tree.itemDoubleClicked.connect(self._tree_item_clicked)
        self._refresh_tree()

        _list = ImageList(self._list_selection_changed, lambda image: self._edit_images([image]),
                          drop_action=self._add_images)
        thumb_list = ThumbnailList(self._list_selection_changed, lambda image: self._edit_images([image]))

        self._tabbed_pane = QtW.QTabWidget()
        self._tabbed_pane.addTab(_list, "List")
        self._tabbed_pane.addTab(thumb_list, "Thumbnails")
        self._tabbed_pane.currentChanged.connect(self._on_tab_changed)

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
        v_box.addWidget(self._tabbed_pane)
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

        self._update_menus()

    # noinspection PyUnresolvedReferences
    def _init_menu(self):
        """Initializes the menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        add_file_item = QtW.QAction("Add &File…", self)
        add_file_item.setIcon(QtG.QIcon("app/icons/image_add.png"))
        add_file_item.setShortcut("Ctrl+F")
        add_file_item.triggered.connect(self._add_image)
        file_menu.addAction(add_file_item)

        add_directory_item = QtW.QAction("Add &Directory…", self)
        add_directory_item.setIcon(QtG.QIcon("app/icons/folder_image.png"))
        add_directory_item.setShortcut("Ctrl+D")
        add_directory_item.triggered.connect(self._add_directory)
        file_menu.addAction(add_directory_item)

        file_menu.addSeparator()

        self._export_item = QtW.QAction("E&xport As Playlist…", self)
        self._export_item.setShortcut("Ctrl+Shift+E")
        self._export_item.triggered.connect(self._export_images)
        # file_menu.addAction(self._export_item)  # Hidden from official release

        file_menu.addSeparator()

        exit_item = QtW.QAction("&Exit", self)
        exit_item.setIcon(QtG.QIcon("app/icons/door_open.png"))
        exit_item.setShortcut("Ctrl+Q")
        exit_item.triggered.connect(QtW.qApp.quit)
        file_menu.addAction(exit_item)

        edit_menu = menubar.addMenu("&Edit")

        edit_tags_item = QtW.QAction("Edit Tags…", self)
        edit_tags_item.setIcon(QtG.QIcon("app/icons/tag_edit.png"))
        edit_tags_item.setShortcut("Ctrl+T")
        edit_tags_item.triggered.connect(self._edit_tags)
        edit_menu.addAction(edit_tags_item)

        edit_menu.addSeparator()

        self._rename_image_item = QtW.QAction("&Rename Image…", self)
        self._rename_image_item.setIcon(QtG.QIcon("app/icons/textfield_rename.png"))
        self._rename_image_item.setShortcut("Ctrl+R")
        self._rename_image_item.triggered.connect(self._rename_image)
        edit_menu.addAction(self._rename_image_item)

        self._replace_image_item = QtW.QAction("&Replace Image…", self)
        self._replace_image_item.setIcon(QtG.QIcon("app/icons/images.png"))
        self._replace_image_item.setShortcut("Ctrl+Shift+R")
        self._replace_image_item.triggered.connect(self._replace_image)
        edit_menu.addAction(self._replace_image_item)

        self._edit_images_item = QtW.QAction("Edit Images…", self)
        self._edit_images_item.setIcon(QtG.QIcon("app/icons/image_edit.png"))
        self._edit_images_item.setShortcut("Ctrl+E")
        self._edit_images_item.triggered.connect(lambda: self._edit_images(self._current_tab().selected_images()))
        edit_menu.addAction(self._edit_images_item)

        self._delete_images_item = QtW.QAction("Delete Images", self)
        self._delete_images_item.setIcon(QtG.QIcon("app/icons/image_delete.png"))
        self._delete_images_item.setShortcut("Delete")
        self._delete_images_item.triggered.connect(self._delete_images)
        edit_menu.addAction(self._delete_images_item)

        options_menu = menubar.addMenu("&Options")

        # noinspection PyArgumentList
        self._load_thumbs_item = QtW.QAction("&Load Thumbnails", checkable=True, checked=config.CONFIG.load_thumbnails)
        self._load_thumbs_item.triggered.connect(self._load_thumbs_item_clicked)
        options_menu.addAction(self._load_thumbs_item)

        thumb_size_item = QtW.QAction("Thumbnail &Size…", self)
        thumb_size_item.triggered.connect(self._thumb_size_item_clicked)
        options_menu.addAction(thumb_size_item)

        help_menu = menubar.addMenu("&Help")

        about_item = QtW.QAction("About", self)
        about_item.setIcon(QtG.QIcon("app/icons/information.png"))
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
        if file is not None:
            self._add_images([file])

    def _add_directory(self):
        """Opens a file chooser then add the images from the selected directory to the database."""
        images = utils.open_directory_chooser(self)
        if images is not None:
            if len(images) == 0:
                utils.show_info("No images in this directory!", parent=self)
            else:
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

    def _rename_image(self):
        """Opens the 'Rename Image' dialog then renames the selected image."""
        images = self._current_tab().selected_images()
        if len(images) == 1:
            image = images[0]
            file_name, ext = os.path.splitext(os.path.basename(image.path))
            text = utils.show_text_input("Enter the new name", "New Name", text=file_name, parent=self)
            if text is not None and file_name != text:
                new_path = utils.slashed(os.path.join(os.path.dirname(image.path), text + ext))
                if not self._dao.update_image_path(image.id, new_path):
                    utils.show_error("Could not rename image!", parent=self)
                else:
                    os.rename(image.path, new_path)
                    self._fetch_images()

    def _replace_image(self):
        """Opens the 'Replace Image' dialog then replaces the image with the selected one."""
        images = self._current_tab().selected_images()
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
        images = self._current_tab().get_images()
        if len(images) > 0:
            file = utils.open_playlist_saver(self)
            if file is not None:
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
        images = self._current_tab().selected_images()

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

    def _fetch_images(self):
        """Fetches images matching the typed query. Starts a search thread to avoid freezing the whole application."""
        tags = self._input_field.text().strip()
        if len(tags) > 0:
            self._ok_btn.setEnabled(False)
            self._input_field.setEnabled(False)
            self._thread = _SearchThread(tags)
            # noinspection PyUnresolvedReferences
            self._thread.finished.connect(self._on_fetch_done)
            self._thread.start()

    _THRESHOLD = 50

    def _on_fetch_done(self):
        """Called when images searching is done."""
        if self._thread.failed:
            utils.show_error(self._thread.error, parent=self)
            self._ok_btn.setEnabled(True)
            self._input_field.setEnabled(True)
        else:
            images = self._thread.fetched_images
            images.sort(key=lambda i: i.path)

            if config.CONFIG.load_thumbnails:
                load_thumbs = True
                if len(images) > self._THRESHOLD:
                    button = utils.show_question(f"Query returned more than {self._THRESHOLD} images, "
                                                 f"thumbnails will be disabled.\nDo you want to load them anyway?",
                                                 title="Load images?", parent=self)
                    if button != QtW.QMessageBox.Yes:
                        load_thumbs = False
            else:
                load_thumbs = False

            for i in range(2):
                tab = self._tabbed_pane.widget(i)
                tab.clear()
                if load_thumbs and config.CONFIG.load_thumbnails or not isinstance(tab, ThumbnailList):
                    for image in images:
                        tab.add_image(image)
            self._ok_btn.setEnabled(True)
            self._input_field.setEnabled(True)
            self._input_field.setFocus()
        self._update_menus()

    def _load_thumbs_item_clicked(self):
        config.CONFIG.load_thumbnails = self._load_thumbs_item.isChecked()
        config.save_config()

    def _thumb_size_item_clicked(self):
        value = utils.show_int_input("Enter the new size", "Thumbnails Size", value=config.CONFIG.thumbnail_size,
                                     min_value=50, max_value=400, parent=self)
        if value is not None:
            config.CONFIG.thumbnail_size = value
            config.save_config()
            self._fetch_and_refresh()

    def _list_selection_changed(self, _):
        self._update_menus()

    def _on_tab_changed(self, _):
        self._update_menus()

    def _update_menus(self):
        selection_size = len(self._current_tab().selected_indexes())
        one_element = selection_size == 1
        list_not_empty = selection_size != 0
        self._export_item.setEnabled(self._current_tab().count() > 0)
        self._rename_image_item.setEnabled(one_element)
        self._replace_image_item.setEnabled(one_element)
        self._edit_images_item.setEnabled(list_not_empty)
        self._delete_images_item.setEnabled(list_not_empty)

    def _current_tab(self) -> ImageListView:
        # noinspection PyTypeChecker
        return self._tabbed_pane.currentWidget()

    @classmethod
    def run(cls):
        """Run an instance of this Application class."""
        try:
            if os.name == "nt":
                # Arbitrary string to display app icon in the taskbar on Windows.
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("image_library")

            config.load_config()

            app = QtW.QApplication(sys.argv)

            da.update_if_needed()

            # Initialize tag types
            tags_dao = da.TagsDao(config.CONFIG.database_path)
            types = tags_dao.get_all_types()
            if types is None:
                utils.show_error("Could not load data! Shutting down.")
                sys.exit(-1)
            model.TagType.init(types)
            tags_dao.close()

            cls().show()
        except BaseException as e:
            logger.exception(e)
            print(e, file=sys.stderr)
            sys.exit(-2)
        else:
            sys.exit(app.exec_())


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
        images_dao = da.ImageDao(config.CONFIG.database_path)
        self._preprocess()
        try:
            expr = queries.query_to_sympy(self._query, simplify=False)
        except ValueError as e:
            self._error = str(e)
            return
        self._images = images_dao.get_images(expr)
        images_dao.close()
        if self._images is None:
            self._error = "Failed to load images!"

    def _preprocess(self):
        meta_tag_values = {}
        index = 0
        # Replace metatag values with placeholders to avoid them being altered in the next step
        while "There are matches":
            match = re.search(fr":\s*({da.ImageDao.METAVALUE_PATTERN})", self._query)
            if match is not None:
                index += 1
                meta_tag_values[index] = match[1]
                self._query = re.sub(re.escape(match[1]), f"%%{index}%%", self._query, count=1)
            else:
                break

        tags_dao = da.TagsDao(config.CONFIG.database_path)
        compound_tags: typ.List[model.CompoundTag] = tags_dao.get_all_tags(tag_class=model.CompoundTag)
        previous_query = ""
        depth = 0
        # Replace compound tags until none are present
        while self._query != previous_query:
            previous_query = self._query
            for tag in compound_tags:
                self._query = re.sub(fr"(\W|^){tag.label}(\W|$)", fr"\1({tag.definition})\2", self._query)
            depth += 1
            if depth >= self._MAXIMUM_DEPTH:
                self._error = f"Maximum recursion depth of {self._MAXIMUM_DEPTH} reached!"
                return

        # Restore placeholders' original values
        for index, value in meta_tag_values.items():
            self._query = self._query.replace(f"%%{index}%%", value, 1)

    @property
    def fetched_images(self) -> typ.List[model.Image]:
        """Returns all fetched images."""
        return self._images

    @property
    def failed(self) -> bool:
        """Returns true if the operation failed."""
        return self._error is not None

    @property
    def error(self) -> typ.Optional[str]:
        """If the operation failed, returns the reason; otherwise returns None."""
        return self._error
