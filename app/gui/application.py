import ctypes
import os
import pathlib
import re
import sys
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW
import sympy as sp

from app import config, constants, data_access as da, model, queries, utils
from app.i18n import translate as _t
from app.logging import logger
from . import components, dialogs, image_list


class Application(QtW.QMainWindow):
    """Application's main class."""

    _PATHS_TAB = 'paths'
    _THUMBS_TAB = 'thumnails'

    def __init__(self):
        super().__init__()

        self._TAB_TITLES = (
            'main_window.tab.paths_list.title',
            'main_window.tab.thumbnails_list.title',
        )

        self._image_dao = da.ImageDao(config.CONFIG.database_path)
        self._tags_dao = da.TagsDao(config.CONFIG.database_path)

        self._operations_dialog_state: typ.Optional[dialogs.OperationsDialog.State] = None

        self.setAcceptDrops(True)
        self._init_ui()
        utils.gui.center(self)

    def _init_ui(self):
        """Initializes the UI."""
        self.setWindowTitle(constants.APP_NAME + ('*' if config.CONFIG.debug else ''))
        self.setWindowIcon(utils.gui.icon('app-icon', use_theme=False))
        self.setGeometry(0, 0, 800, 600)
        self.setMinimumSize(400, 200)

        self._init_menu()

        self.setCentralWidget(QtW.QWidget(parent=self))

        self._tag_tree = components.TagTree(self._on_delete_item, self._on_insert_tag, parent=self)

        path_list = image_list.ImageList(self._list_selection_changed, lambda image: self._edit_images([image]),
                                         parent=self)
        thumb_list = image_list.ThumbnailList(self._list_selection_changed, lambda image: self._edit_images([image]),
                                              parent=self)

        self._tabbed_pane = QtW.QTabWidget(parent=self)
        self._tabbed_pane.addTab(path_list, _t(self._TAB_TITLES[0], images_number=0))
        self._tabbed_pane.setTabWhatsThis(0, self._PATHS_TAB)
        self._tabbed_pane.addTab(thumb_list, _t(self._TAB_TITLES[1], images_number=0))
        self._tabbed_pane.setTabWhatsThis(1, self._THUMBS_TAB)
        self._tabbed_pane.currentChanged.connect(self._on_tab_changed)

        self._search_btn = QtW.QPushButton(
            utils.gui.icon('search'),
            _t('main_window.query_form.search_button.label'),
            parent=self
        )
        self._search_btn.clicked.connect(lambda: self._fetch_images())

        self._input_field = components.AutoCompleteLineEdit(parent=self)
        self._input_field.setPlaceholderText(_t('main_window.query_form.text_field.placeholder'))
        self._input_field.returnPressed.connect(lambda: self._fetch_images())

        splitter = QtW.QSplitter(parent=self)

        left_layout = QtW.QHBoxLayout()
        left_layout.addWidget(self._tag_tree)
        left_layout.setContentsMargins(5, 5, 0, 5)

        h_box = QtW.QHBoxLayout()
        h_box.addWidget(self._input_field)
        h_box.addWidget(self._search_btn)

        v_box = QtW.QVBoxLayout()
        v_box.addWidget(self._tabbed_pane)
        v_box.addLayout(h_box)
        v_box.setContentsMargins(0, 5, 5, 5)

        left = QtW.QWidget(parent=self)
        left.setLayout(left_layout)
        right = QtW.QWidget(parent=self)
        right.setLayout(v_box)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([100, 500])

        self.setCentralWidget(splitter)

        self._input_field.setFocus()

        self._update_menus()
        self._refresh_tree()

    # noinspection PyUnresolvedReferences
    def _init_menu(self):
        """Initializes the menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu(_t('main_window.menu.file.label'))

        file_menu.addAction(
            utils.gui.icon('insert-image'),
            _t('main_window.menu.file.item.add_files'),
            self._add_image,
            'Ctrl+F'
        )
        file_menu.addAction(
            utils.gui.icon('folder-add'),
            _t('main_window.menu.file.item.add_directory'),
            self._add_directory,
            'Ctrl+D'
        )
        file_menu.addSeparator()
        self._export_item = file_menu.addAction(
            utils.gui.icon('document-save-as'),
            _t('main_window.menu.file.item.export_playlist'),
            self._export_images,
            'Ctrl+Shift+E'
        )
        file_menu.addSeparator()
        file_menu.addAction(
            utils.gui.icon('application-exit'),
            _t('main_window.menu.file.item.exit'),
            QtW.qApp.quit,
            'Ctrl+Q'
        )

        edit_menu = menubar.addMenu(_t('main_window.menu.edit.label'))

        edit_menu.addAction(
            utils.gui.icon('tag-edit'),
            _t('main_window.menu.edit.item.edit_tags'),
            self._edit_tags,
            'Ctrl+T'
        )
        edit_menu.addSeparator()
        self._rename_image_item = edit_menu.addAction(
            utils.gui.icon('document-edit'),
            _t('main_window.menu.edit.item.rename_image'),
            self._rename_image,
            'Ctrl+R'
        )
        self._replace_image_item = edit_menu.addAction(
            utils.gui.icon('image-replace'),
            _t('main_window.menu.edit.item.replace_image'),
            self._replace_image,
            'Ctrl+Shift+R'
        )
        self._move_images_item = edit_menu.addAction(
            utils.gui.icon('edit-move'),
            _t('main_window.menu.edit.item.move_images'),
            self._move_images,
            'Ctrl+M'
        )
        self._edit_images_item = edit_menu.addAction(
            utils.gui.icon('image-edit'),
            _t('main_window.menu.edit.item.edit_images'),
            lambda: self._edit_images(self._current_tab().selected_images()),
            'Ctrl+E'
        )
        self._delete_images_item = edit_menu.addAction(
            utils.gui.icon('edit-delete'),
            _t('main_window.menu.edit.item.delete_images'),
            self._delete_images,
            'Delete'
        )

        tools_menu = menubar.addMenu(_t('main_window.menu.tools.label'))

        tools_menu.addAction(
            utils.gui.icon('tag-missing'),
            _t('main_window.menu.tools.item.tagless_images'),
            lambda: self._fetch_images(tagless_images=True)
        )
        tools_menu.addSeparator()
        tools_menu.addAction(
            utils.gui.icon('system-run'),
            _t('main_window.menu.tools.item.perform_operations'),
            self._apply_transformation,
            'Ctrl+O'
        )
        tools_menu.addAction(
            utils.gui.icon('utilities-terminal'),
            _t('main_window.menu.tools.item.SQL_terminal'),
            self._open_sql_terminal,
            'Ctrl+Shift+T'
        )

        help_menu = menubar.addMenu(_t('main_window.menu.help.label'))

        help_menu.addAction(
            utils.gui.icon('configure-application'),
            _t('main_window.menu.help.item.settings'),
            self._show_settings_dialog,
            'Ctrl+Alt+S'
        )
        help_menu.addAction(
            utils.gui.icon('help-about'),
            _t('main_window.menu.help.item.about'),
            lambda: dialogs.AboutDialog(self).show()
        )

    def _center(self):
        """Centers the application window."""
        qr = self.frameGeometry()
        cp = QtW.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _move_images(self):
        images = self._current_tab().selected_images()
        dialog = dialogs.MoveImagesDialog(images, parent=self)
        dialog.set_on_close_action(lambda _: self._fetch_images())
        dialog.show()

    def _apply_transformation(self):
        def _on_close(dialog: dialogs.OperationsDialog):
            self._operations_dialog_state = dialog.state
            self._fetch_images()

        dialog = dialogs.OperationsDialog(state=self._operations_dialog_state, parent=self)
        dialog.set_on_close_action(_on_close)
        dialog.show()

    def _open_sql_terminal(self):
        dialog = dialogs.CommandLineDialog(parent=self)
        dialog.set_on_close_action(lambda _: self._fetch_and_refresh())
        dialog.show()

    def _show_settings_dialog(self):
        settings_dialog = dialogs.SettingsDialog(parent=self)
        settings_dialog.set_on_close_action(lambda _: self._fetch_and_refresh())
        settings_dialog.show()

    def _add_image(self):
        """Opens a file chooser then adds the selected images to the database."""
        files = utils.gui.open_file_chooser(single_selection=False, mode=utils.gui.FILTER_IMAGES, parent=self)
        if files is not None:
            if len(files) == 0:
                utils.gui.show_info(_t('popup.no_files_selected.text'), parent=self)
            else:
                self._add_images(files)

    def _add_directory(self):
        """Opens a file chooser then adds the images from the selected directory to the database."""
        files = utils.gui.open_directory_chooser(parent=self)
        if files is not None:
            if len(files) == 0:
                utils.gui.show_info(_t('popup.empty_directory.text'), parent=self)
            else:
                self._add_images(files)

    def _add_images(self, image_paths: typ.List[pathlib.Path]):
        """Opens the 'Add Images' dialog then adds the images to the database.
        Checks for potential duplicates.
        """
        if image_paths:
            similarities = {i: s for i in image_paths
                            if (s := self._image_dao.image_registered(i)) != self._image_dao.IMG_NOT_REGISTERED}
            registered = [s == self._image_dao.IMG_REGISTERED for s in similarities.values()]

            if registered and all(registered):  # If list is empty, all() returns True
                if len(registered) > 1:
                    text = _t('popup.images_registered.text')
                else:
                    text = _t('popup.image_registered.text')
                utils.gui.show_info(text, parent=self)
                return

            if any(registered):
                utils.gui.show_info(_t('popup.some_images_registered.text'), parent=self)

            add_all = True
            similar = map(lambda s: s == self._image_dao.IMG_SIMILAR, similarities.values())
            if any(similar):
                if len(image_paths) > 1:
                    text = _t('popup.similar_images_found.text')
                else:
                    text = _t('popup.similar_image_found.text')
                add_all = utils.gui.show_question(text, cancel=True, parent=self)

            if add_all is not None:
                images_to_add = []
                for i in image_paths:
                    s = similarities.get(i)
                    if s != self._image_dao.IMG_REGISTERED and (add_all or s != self._image_dao.IMG_SIMILAR):
                        images_to_add.append(model.Image(id=0, path=i, hash=utils.image.get_hash(i)))

                if images_to_add:
                    dialog = dialogs.EditImageDialog(self._image_dao, self._tags_dao, show_skip=len(images_to_add) > 1,
                                                     mode=dialogs.EditImageDialog.ADD, parent=self)
                    dialog.set_on_close_action(lambda _: self._fetch_and_refresh())
                    dialog.set_images(images_to_add, {})
                    dialog.show()

    def _rename_image(self):
        """Opens the 'Rename Image' dialog then renames the selected image."""
        images = self._current_tab().selected_images()
        if len(images) == 1:
            image = images[0]
            file_name, ext = os.path.splitext(image.path.name)
            new_name = utils.gui.show_text_input(_t('popup.rename_image.text'), _t('popup.rename_image.title'),
                                                 text=file_name, parent=self)
            if new_name is not None and file_name != new_name:
                new_path = image.path.parent / (new_name + ext)
                if not self._image_dao.update_image(image.id, new_path, image.hash):
                    utils.gui.show_error(_t('popup.rename_error.text'), parent=self)
                else:
                    rename = True
                    if new_path.exists():
                        rename &= utils.gui.show_question(_t('popup.rename_overwrite.text'),
                                                          _t('popup.rename_overwrite.title'),
                                                          parent=self)
                    if rename:
                        try:
                            image.path.rename(new_path)
                        except OSError:
                            utils.gui.show_error(_t('popup.rename_file_error.text'), parent=self)
                            # Rollback changes
                            self._image_dao.update_image(image.id, image.path, image.hash)
                        self._fetch_images()

    def _replace_image(self):
        """Opens the 'Replace Image' dialog then replaces the image with the selected one."""
        images = self._current_tab().selected_images()
        if len(images) == 1:
            image = images[0]
            dialog = dialogs.EditImageDialog(self._image_dao, self._tags_dao, mode=dialogs.EditImageDialog.REPLACE,
                                             parent=self)
            dialog.set_on_close_action(lambda _: self._fetch_images())
            tags = self._image_dao.get_image_tags(image.id, self._tags_dao)
            if tags is None:
                utils.gui.show_error(_t('popup.tag_load_error.text'))
            dialog.set_image(image, tags)
            dialog.show()

    def _export_images(self):
        """Opens a file saver then writes all images to a playlist file."""
        images = self._current_tab().get_images()
        if len(images) > 0:
            file = utils.gui.open_playlist_saver(parent=self)
            if file:
                da.write_playlist(file, images)
                utils.gui.show_info(_t('popup.playlist_exported.text'), parent=self)

    def _fetch_and_refresh(self):
        """Fetches images then refreshes the list."""
        self._fetch_images()
        self._refresh_tree()

    def _edit_images(self, images: typ.List[model.Image]):
        """Opens the 'Edit Images' dialog then updates all edited images."""
        if len(images) > 0:
            dialog = dialogs.EditImageDialog(self._image_dao, self._tags_dao, show_skip=len(images) > 1, parent=self)
            dialog.set_on_close_action(lambda _: self._fetch_and_refresh())
            tags = {}
            for image in images:
                t = self._image_dao.get_image_tags(image.id, self._tags_dao)
                if t is None:
                    utils.gui.show_error(_t('popup.tag_load_error.text'), parent=self)
                tags[image.id] = t
            dialog.set_images(images, tags)
            dialog.show()

    def _delete_images(self):
        """Deletes the selected images. User is asked to confirm the action."""
        images = self._current_tab().selected_images()

        if len(images) > 0:
            dialog = dialogs.DeleteFileConfirmDialog(len(images), parent=self)
            delete = dialog.exec_()
            delete_from_disk = delete and dialog.delete_from_disk()
            if delete:
                errors = []
                for item in images:
                    ok = self._image_dao.delete_image(item.id)
                    if ok and delete_from_disk:
                        try:
                            item.path.unlink()
                        except OSError as e:
                            logger.exception(e)
                            errors.append(str(item.path))
                if errors:
                    utils.gui.show_error(_t('popup.delete_image_error.text', files='\n'.join(errors)), parent=self)
                self._fetch_images()

    def _edit_tags(self):
        """Opens the 'Edit Tags' dialog. Tags tree is refreshed afterwards."""
        dialog = dialogs.EditTagsDialog(self._tags_dao, parent=self)
        dialog.set_on_close_action(lambda _: self._refresh_tree())
        dialog.show()

    def _on_delete_item(self, item: QtW.QTreeWidgetItem):
        """Called when a tag or tag type from the tags tree has to be deleted.
        Asks for user confirmation.

        :param item: The item to delete.
        """
        o = item.data(0, components.TagTree.DATA_OBJECT)
        label = components.TagTree.get_item_label(item)
        if item.whatsThis(0) == components.TagTree.TAG_TYPE:
            delete = utils.gui.show_question(_t('popup.delete_tag_type_confirm.text', label=label), parent=self)
            if delete:
                self._tags_dao.delete_type(o.id)
                self._refresh_tree()
        else:
            delete = utils.gui.show_question(_t('popup.delete_tag_confirm.text', label=label), parent=self)
            if delete:
                self._tags_dao.delete_tag(o.id)
                self._refresh_tree()

    def _on_insert_tag(self, item: QtW.QTreeWidgetItem):
        """Called when a tag from the tags tree has to be inserted.

        :param item: The item to insert.
        """
        self._input_field.setText((self._input_field.text() + ' ' + item.text(0)).lstrip())

    def _update_completer(self):
        """Resets the query completer with all current tags."""
        tags = map(lambda t: t.label, self._tags_dao.get_all_tags(sort_by_label=True))
        self._input_field.set_completer_model(tags)

    def _refresh_tree(self, *_):
        """Refreshes the tags tree."""
        self._tag_tree.refresh(self._tags_dao.get_all_tag_types(), self._tags_dao.get_all_tags())
        self._update_completer()

    def _fetch_images(self, tagless_images: bool = False):
        """Fetches images matching the typed query. Starts a search thread to avoid freezing the whole application.

        :param tagless_images: Whether to fetch tagless images. If True, the query is ignored.
        """
        tags = self._input_field.text().strip()
        if len(tags) > 0 or tagless_images:
            self._search_btn.setEnabled(False)
            self._input_field.setEnabled(False)
            self._thread = _SearchThread(tags, tagless_images=tagless_images)
            self._thread.finished.connect(self._on_fetch_done)
            self._thread.start()

    def _on_fetch_done(self):
        """Called when image searching is done."""
        if self._thread.failed:
            utils.gui.show_error(self._thread.error, parent=self)
            self._search_btn.setEnabled(True)
            self._input_field.setEnabled(True)
        else:
            images = self._thread.fetched_images
            images.sort(key=lambda i: i.path)

            if config.CONFIG.load_thumbnails:
                load_thumbs = True
                if len(images) > config.CONFIG.thumbnail_load_threshold:
                    ok = utils.gui.show_question(
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
                nb = len(images) if self._tabbed_pane.tabWhatsThis(i) != self._THUMBS_TAB or load_thumbs else 0
                self._tabbed_pane.setTabText(i, _t(self._TAB_TITLES[i], images_number=nb))
                tab.clear()
                if load_thumbs and config.CONFIG.load_thumbnails or not isinstance(tab, image_list.ThumbnailList):
                    for image in images:
                        tab.add_image(image)
            self._search_btn.setEnabled(True)
            self._input_field.setEnabled(True)
            self._input_field.setFocus()
        self._update_menus()

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
        self._move_images_item.setEnabled(list_not_empty)

    def _current_tab(self) -> image_list.ImageListView:
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
                if utils.files.accept_image_files(urls):
                    event.accept()
                else:
                    event.ignore()
        else:
            event.ignore()

    @staticmethod
    def _get_urls(event: QtG.QDropEvent) -> typ.List[pathlib.Path]:
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
            urls.append(pathlib.Path(url.toLocalFile()).absolute())
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
            success, message = da.update_database_if_needed()
            if success is None:  # Update cancelled
                if message:
                    utils.gui.show_info(message)
                sys.exit(-2)
            elif not success:  # Update failed
                utils.gui.show_error(message)
                sys.exit(-3)
            else:
                if message:  # Update successed
                    utils.gui.show_info(message)
                cls().show()
                sys.exit(app.exec_())
        except SystemExit:
            raise
        except BaseException as e:
            logger.exception(e)
            print(e, file=sys.stderr)
            sys.exit(-1)


class _SearchThread(QtC.QThread):
    """This thread is used to search images from a query."""

    _MAXIMUM_DEPTH = 20

    def __init__(self, query: str = None, tagless_images: bool = False):
        """Creates a search thread for a query.

        :param query: The query.
        :param tagless_images: Whether to fetch tagless images. If True, the query is ignored.
        """
        super().__init__()
        self._query = query
        self._tagless_images = tagless_images
        self._images = []
        self._error = None

    def run(self):
        # Cannot use application’s as SQLite connections cannot be shared between threads
        images_dao = da.ImageDao(config.CONFIG.database_path)
        if not self._tagless_images:
            self._preprocess()

        if not self._error:
            expr = sp.true
            try:
                if not self._tagless_images:
                    expr = queries.query_to_sympy(self._query, simplify=True)
            except ValueError as e:
                self._error = str(e)
            else:
                if not self._tagless_images:
                    self._images = images_dao.get_images(expr)
                else:
                    self._images = images_dao.get_tagless_images()
                images_dao.close()
                if self._images is None:
                    self._error = _t('thread.search.error.image_loading_error')

    def _preprocess(self):
        meta_tag_values = {}
        index = 0
        # Replace metatag values with placeholders to avoid them being altered in the next step
        while 'there are matches':
            # In-quotes pattern *MUST* be the same as PLAIN_TEXT and REGEX in grammar.lark file
            if match := re.search(fr'(\w+\s*:\s*(["/])((\\\\)*|(.*?[^\\](\\\\)*))\2)', self._query):
                index += 1
                meta_tag_values[index] = match[1]
                # noinspection PyUnresolvedReferences
                self._query = re.sub(re.escape(match[1]), f'%%{index}%%', self._query, count=1)
            else:
                break

        # Cannot use application’s as SQLite connections cannot be shared between threads
        tags_dao = da.TagsDao(config.CONFIG.database_path)
        compound_tags = tags_dao.get_all_tags(tag_class=model.CompoundTag)
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

        # Restore placeholders’ original values
        for index, value in meta_tag_values.items():
            self._query = self._query.replace(f'%%{index}%%', value, 1)

    @property
    def fetched_images(self) -> typ.List[model.Image]:
        """Returns all fetched images."""
        return self._images

    @property
    def failed(self) -> bool:
        """Returns True if the operation failed."""
        return self._error is not None

    @property
    def error(self) -> typ.Optional[str]:
        """If the operation failed, returns the reason; otherwise returns None."""
        return self._error
