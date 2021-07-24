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
from ..i18n import translate as _t
from ..logging import logger


class Application(QtW.QMainWindow):
    """Application's main class."""

    # noinspection PyArgumentList
    def __init__(self):
        super().__init__()

        self._TAB_TITLES = (
            'main_window.tab.paths_list.title',
            'main_window.tab.thumbnails_list.title',
        )

        self._dao = da.ImageDao(config.CONFIG.database_path)
        self._tags_dao = da.TagsDao(config.CONFIG.database_path)

        self.setAcceptDrops(True)
        self._init_ui()
        utils.center(self)

    # noinspection PyUnresolvedReferences,PyArgumentList
    def _init_ui(self):
        """Initializes the UI."""
        self.setWindowTitle(_t('main_window.title'))
        self.setWindowIcon(QtG.QIcon(constants.ICONS_DIR + 'app_icon.png'))
        self.setGeometry(0, 0, 800, 600)
        self.setMinimumSize(400, 200)

        self._init_menu()

        self.setCentralWidget(QtW.QWidget())

        self._tag_tree = TagTree()
        self._tag_tree.itemDoubleClicked.connect(self._tree_item_clicked)
        self._refresh_tree()

        path_list = ImageList(self._list_selection_changed, lambda image: self._edit_images([image]))
        thumb_list = ThumbnailList(self._list_selection_changed, lambda image: self._edit_images([image]))

        self._tabbed_pane = QtW.QTabWidget()
        self._tabbed_pane.addTab(path_list, _t(self._TAB_TITLES[0], images_number=0))
        self._tabbed_pane.addTab(thumb_list, _t(self._TAB_TITLES[1], images_number=0))
        self._tabbed_pane.currentChanged.connect(self._on_tab_changed)

        self._ok_btn = QtW.QPushButton(_t('main_window.query_form.ok_button.label'))
        self._ok_btn.clicked.connect(self._fetch_images)

        self._input_field = QtW.QLineEdit()
        self._input_field.setPlaceholderText(_t('main_window.query_form.text_field.placeholder'))
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

        file_menu = menubar.addMenu(_t('main_window.menu.file.label'))

        add_file_item = QtW.QAction(_t('main_window.menu.file.items.add_file'), self)
        add_file_item.setIcon(QtG.QIcon(constants.ICONS_DIR + 'image_add.png'))
        add_file_item.setShortcut('Ctrl+F')
        add_file_item.triggered.connect(self._add_image)
        file_menu.addAction(add_file_item)

        add_directory_item = QtW.QAction(_t('main_window.menu.file.items.add_directory'), self)
        add_directory_item.setIcon(QtG.QIcon(constants.ICONS_DIR + 'folder_image.png'))
        add_directory_item.setShortcut('Ctrl+D')
        add_directory_item.triggered.connect(self._add_directory)
        file_menu.addAction(add_directory_item)

        file_menu.addSeparator()

        self._export_item = QtW.QAction(_t('main_window.menu.file.items.export_playlist'), self)
        self._export_item.setShortcut('Ctrl+Shift+E')
        self._export_item.triggered.connect(self._export_images)
        file_menu.addAction(self._export_item)

        file_menu.addSeparator()

        exit_item = QtW.QAction(_t('main_window.menu.file.items.exit'), self)
        exit_item.setIcon(QtG.QIcon(constants.ICONS_DIR + 'door_open.png'))
        exit_item.setShortcut('Ctrl+Q')
        exit_item.triggered.connect(QtW.qApp.quit)
        file_menu.addAction(exit_item)

        edit_menu = menubar.addMenu(_t('main_window.menu.edit.label'))

        edit_tags_item = QtW.QAction(_t('main_window.menu.edit.items.edit_tags'), self)
        edit_tags_item.setIcon(QtG.QIcon(constants.ICONS_DIR + 'tag_edit.png'))
        edit_tags_item.setShortcut('Ctrl+T')
        edit_tags_item.triggered.connect(self._edit_tags)
        edit_menu.addAction(edit_tags_item)

        edit_menu.addSeparator()

        self._rename_image_item = QtW.QAction(_t('main_window.menu.edit.items.rename_image'), self)
        self._rename_image_item.setIcon(QtG.QIcon(constants.ICONS_DIR + 'textfield_rename.png'))
        self._rename_image_item.setShortcut('Ctrl+R')
        self._rename_image_item.triggered.connect(self._rename_image)
        edit_menu.addAction(self._rename_image_item)

        self._replace_image_item = QtW.QAction(_t('main_window.menu.edit.items.replace_image'), self)
        self._replace_image_item.setIcon(QtG.QIcon(constants.ICONS_DIR + 'images.png'))
        self._replace_image_item.setShortcut('Ctrl+Shift+R')
        self._replace_image_item.triggered.connect(self._replace_image)
        edit_menu.addAction(self._replace_image_item)

        self._edit_images_item = QtW.QAction(_t('main_window.menu.edit.items.edit_images'), self)
        self._edit_images_item.setIcon(QtG.QIcon(constants.ICONS_DIR + 'image_edit.png'))
        self._edit_images_item.setShortcut('Ctrl+E')
        self._edit_images_item.triggered.connect(lambda: self._edit_images(self._current_tab().selected_images()))
        edit_menu.addAction(self._edit_images_item)

        self._delete_images_item = QtW.QAction(_t('main_window.menu.edit.items.delete_images'), self)
        self._delete_images_item.setIcon(QtG.QIcon(constants.ICONS_DIR + 'image_delete.png'))
        self._delete_images_item.setShortcut('Delete')
        self._delete_images_item.triggered.connect(self._delete_images)
        edit_menu.addAction(self._delete_images_item)

        options_menu = menubar.addMenu(_t('main_window.menu.options.label'))

        # noinspection PyArgumentList
        self._load_thumbs_item = QtW.QAction(_t('main_window.menu.options.items.load_thumbs'), checkable=True,
                                             checked=config.CONFIG.load_thumbnails)
        self._load_thumbs_item.triggered.connect(self._load_thumbs_item_clicked)
        options_menu.addAction(self._load_thumbs_item)

        thumb_size_item = QtW.QAction(_t('main_window.menu.options.items.thumbs_size'), self)
        thumb_size_item.triggered.connect(self._thumb_size_item_clicked)
        options_menu.addAction(thumb_size_item)

        thumb_load_threshold_item = QtW.QAction(_t('main_window.menu.options.items.thumbs_load_threshold'), self)
        thumb_load_threshold_item.triggered.connect(self._thumb_load_threshold_item_clicked)
        options_menu.addAction(thumb_load_threshold_item)

        help_menu = menubar.addMenu(_t('main_window.menu.help.label'))

        about_item = QtW.QAction(_t('main_window.menu.help.items.about'), self)
        about_item.setIcon(QtG.QIcon(constants.ICONS_DIR + 'information.png'))
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
                utils.show_info(_t('popup.empty_directory.text'), parent=self)
            else:
                self._add_images(images)

    def _add_images(self, images: typ.List[str]):
        """Opens the 'Add Images' dialog then adds the images to the database. Checks for duplicates."""
        if len(images) > 0:
            images_to_add = [i for i in images if not self._dao.image_registered(i)]
            if len(images_to_add) == 0:
                text = _t('popup.images_already_registered.text')
                utils.show_info(text, parent=self)
            else:
                dialog = EditImageDialog(self, show_skip=len(images_to_add) > 1, mode=EditImageDialog.ADD)
                dialog.set_on_close_action(self._fetch_and_refresh)
                dialog.set_images([model.Image(id=0, path=image_path) for image_path in images_to_add], {})
                dialog.show()

    def _rename_image(self):
        """Opens the 'Rename Image' dialog then renames the selected image."""
        images = self._current_tab().selected_images()
        if len(images) == 1:
            image = images[0]
            file_name, ext = os.path.splitext(os.path.basename(image.path))
            text = utils.show_text_input(_t('popup.rename_image.text'), _t('popup.rename_image.title'),
                                         text=file_name, parent=self)
            if text is not None and file_name != text:
                new_path = utils.slashed(os.path.join(os.path.dirname(image.path), text + ext))
                if not self._dao.update_image_path(image.id, new_path):
                    utils.show_error(_t('popup.rename_error.text'), parent=self)
                else:
                    rename = True
                    if os.path.exists(new_path):
                        rename &= utils.show_question(_t('popup.rename_overwrite.text'),
                                                      _t('popup.rename_overwrite.title'), parent=self)
                    if rename:
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
                utils.show_error(_t('popup.tag_load_error.text'))
            dialog.set_image(image, tags)
            dialog.show()

    def _export_images(self):
        """Opens a file saver then writes all images to a playlist file."""
        images = self._current_tab().get_images()
        if len(images) > 0:
            file = utils.open_playlist_saver(self)
            if file is not None:
                da.write_playlist(file, images)
                utils.show_info(_t('popup.playlist_exported.text'), parent=self)

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
                    utils.show_error(_t('popup.tag_load_error.text'))
                tags[image.id] = t
            dialog.set_images(images, tags)
            dialog.show()

    def _delete_images(self):
        """Deletes the selected images. User is asked to confirm the action."""
        images = self._current_tab().selected_images()

        if len(images) > 0:
            if len(images) > 1:
                message = '<html>' + _t('popup.delete_image_warning.text_question_multiple')
            else:
                message = '<html>' + _t('popup.delete_image_warning.text_question_single')
            message += '<br/><b>' + _t('popup.delete_image_warning.text_warning') + '</b></html>'
            if utils.show_question(message, _t('popup.delete_image_warning.title'), parent=self):
                for item in images:
                    if self._dao.delete_image(item.id):
                        try:
                            os.remove(item.path)
                        except FileNotFoundError as e:  # TODO display a single message with all file name in a textarea
                            logger.exception(e)
                            utils.show_error(_t('popup.delete_image_error.text', filename=e.filename), parent=self)
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
        if item.whatsThis(0) == 'tag':
            self._input_field.setText((self._input_field.text() + ' ' + item.text(0)).lstrip())

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
                if len(images) > config.CONFIG.thumbnail_load_threshold:
                    ok = utils.show_question(
                        _t('popup.load_thumbs_warning.text', threshold=config.CONFIG.thumbnail_load_threshold),
                        _t('popup.load_thumbs_warning.title'),
                        parent=self
                    )
                    if not ok:
                        load_thumbs = False
            else:
                load_thumbs = False

            for i in range(2):
                tab = self._tabbed_pane.widget(i)
                self._tabbed_pane.setTabText(i, _t(self._TAB_TITLES[i], images_number=len(images)))
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
        value = utils.show_int_input(
            _t('popup.set_thumbs_size.text', min=constants.MIN_THUMB_SIZE, max=constants.MAX_THUMB_SIZE),
            _t('popup.set_thumbs_size.title'),
            value=config.CONFIG.thumbnail_size,
            min_value=constants.MIN_THUMB_SIZE,
            max_value=constants.MAX_THUMB_SIZE,
            parent=self
        )
        if value is not None:
            config.CONFIG.thumbnail_size = value
            config.save_config()
            self._fetch_and_refresh()

    def _thumb_load_threshold_item_clicked(self):
        value = utils.show_int_input(
            _t('popup.set_thumbs_load_threshold.text',
               min=constants.MIN_THUMB_LOAD_THRESHOLD,
               max=constants.MAX_THUMB_LOAD_THRESHOLD),
            _t('popup.set_thumbs_load_threshold.title'),
            value=config.CONFIG.thumbnail_load_threshold,
            min_value=constants.MIN_THUMB_LOAD_THRESHOLD,
            max_value=constants.MAX_THUMB_LOAD_THRESHOLD,
            parent=self
        )
        if value is not None:
            config.CONFIG.thumbnail_load_threshold = value
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

    def dragEnterEvent(self, event: QtG.QDragEnterEvent):
        self._check_drag(event)

    def dragMoveEvent(self, event: QtG.QDragMoveEvent):
        self._check_drag(event)

    def dropEvent(self, event: QtG.QDropEvent):
        # No need to check for ValueError of _get_urls as it is already handled in dragEnterEvent and dragMoveEvent
        self._add_images(self._get_urls(event))

    @staticmethod
    def _check_drag(event: QtG.QDragMoveEvent):
        """
        Checks the validity of files dragged into this list. If at least one file has an extension that is not in the
        config.FILE_EXTENSION array, the event is cancelled.

        :param event: The drag event.
        """
        if event.mimeData().hasUrls():
            try:
                urls = Application._get_urls(event)
            except ValueError:
                event.ignore()
            else:
                if all(map(lambda f: os.path.splitext(f)[1].lower()[1:] in constants.FILE_EXTENSIONS, urls)):
                    event.accept()
                else:
                    event.ignore()
        else:
            event.ignore()

    @staticmethod
    def _get_urls(event: QtG.QDropEvent) -> typ.List[str]:
        """
        Extracts all file URLs from the drop event.

        :param event: The drop event.
        :return: URLs of dropped files.
        :raises ValueError: If one of the URLs is not a local file.
        """
        urls = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                raise ValueError(_t('main_window.error.remote_URL'))
            urls.append(url.toLocalFile())
        return urls

    @classmethod
    def run(cls):
        """Run an instance of this Application class."""
        try:
            if os.name == 'nt':
                # Arbitrary string to display app icon in the taskbar on Windows.
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('image_library')

            config.load_config()

            app = QtW.QApplication(sys.argv)

            da.update_if_needed()

            # Initialize tag types
            tags_dao = da.TagsDao(config.CONFIG.database_path)
            types = tags_dao.get_all_types()
            if types is None:
                utils.show_error(_t('popup.data_loading_error.text'))
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
        """Creates a search thread for a query.

        :param query: The query.
        """
        super().__init__()
        self._query = query
        self._images = []
        self._error = None

    def run(self):
        images_dao = da.ImageDao(config.CONFIG.database_path)
        self._preprocess()
        if not self._error:
            try:
                expr = queries.query_to_sympy(self._query, simplify=False)
            except ValueError as e:
                self._error = str(e)
            else:
                self._images = images_dao.get_images(expr)
                images_dao.close()
                if self._images is None:
                    self._error = _t('thread.search.error.image_loading_error')

    def _preprocess(self):
        meta_tag_values = {}
        index = 0
        # Replace metatag values with placeholders to avoid them being altered in the next step
        while 'there are matches':
            if match := re.search(fr'(\w+\s*:\s*{da.ImageDao.METAVALUE_PATTERN})', self._query):
                index += 1
                meta_tag_values[index] = match[1]
                # noinspection PyUnresolvedReferences
                self._query = re.sub(re.escape(match[1]), f'%%{index}%%', self._query, count=1)
            else:
                break

        tags_dao = da.TagsDao(config.CONFIG.database_path)
        # noinspection PyTypeChecker
        compound_tags: typ.List[model.CompoundTag] = tags_dao.get_all_tags(tag_class=model.CompoundTag)
        previous_query = ''
        depth = 0
        # Replace compound tags until none are present
        while self._query != previous_query:
            previous_query = self._query
            for tag in compound_tags:
                self._query = re.sub(fr'(\W|^){tag.label}(\W|$)', fr'\1({tag.definition})\2', self._query)
            depth += 1
            if depth >= self._MAXIMUM_DEPTH:
                self._error = _t('thread.search.error.max_recursion', max_depth=self._MAXIMUM_DEPTH)
                return

        # Restore placeholders' original values
        for index, value in meta_tag_values.items():
            self._query = self._query.replace(f'%%{index}%%', value, 1)

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
