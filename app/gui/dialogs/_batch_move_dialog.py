from __future__ import annotations

import os
import shutil
import sqlite3
import typing as typ

import PyQt5.QtWidgets as QtW

from app import utils, data_access, config, queries
from app.i18n import translate as _t
from . import _dialog_base
from .. import components, threads


class BatchMoveDialog(_dialog_base.Dialog):
    """This dialog provides tools to apply transformations to images."""

    def __init__(self, parent: typ.Optional[QtW.QWidget] = None):
        super().__init__(parent=parent, title=_t('dialog.batch_move.title'), modal=True,
                         mode=_dialog_base.Dialog.CLOSE)
        self._update_ui()

    def _init_body(self):
        layout = QtW.QVBoxLayout()

        self._list_warning_label = components.LabelWithIcon(
            utils.gui.icon('warning_small'),
            _t('dialog.batch_move.list_empty'),
            parent=self
        )
        retain_size = self._list_warning_label.sizePolicy()
        retain_size.setRetainSizeWhenHidden(True)
        self._list_warning_label.setSizePolicy(retain_size)
        layout.addWidget(self._list_warning_label)

        # List buttons and label
        list_buttons_layout = QtW.QHBoxLayout()

        list_buttons_layout.addWidget(QtW.QLabel(_t('dialog.batch_move.files_and_directories'), parent=self), stretch=1)

        self._choose_files_button = QtW.QPushButton(utils.gui.icon('image_add'), '', parent=self)
        self._choose_files_button.setToolTip(_t('dialog.batch_move.add_files_button.tooltip'))
        self._choose_files_button.clicked.connect(lambda: self._add_files_or_directories(select_files=True))
        list_buttons_layout.addWidget(self._choose_files_button)

        self._choose_dirs_button = QtW.QPushButton(utils.gui.icon('add_directory'), '', parent=self)
        self._choose_dirs_button.setToolTip(_t('dialog.batch_move.add_directory_button.tooltip'))
        self._choose_dirs_button.clicked.connect(lambda: self._add_files_or_directories(select_files=False))
        list_buttons_layout.addWidget(self._choose_dirs_button)

        self._delete_items_button = QtW.QPushButton(utils.gui.icon('cross'), '', parent=self)
        self._delete_items_button.setToolTip(_t('dialog.batch_move.delete_item_button.tooltip'))
        self._delete_items_button.clicked.connect(self._delete_selected_rows)
        list_buttons_layout.addWidget(self._delete_items_button)

        self._clear_list_button = QtW.QPushButton(utils.gui.icon('clear_list'), '', parent=self)
        self._clear_list_button.setToolTip(_t('dialog.batch_move.clear_list_button.tooltip'))
        self._clear_list_button.clicked.connect(lambda: self._list.clear())
        list_buttons_layout.addWidget(self._clear_list_button)

        layout.addLayout(list_buttons_layout)

        # List
        self._list = QtW.QListWidget(parent=self)
        self._list.setSelectionMode(QtW.QAbstractItemView.ExtendedSelection)
        self._list.selectionModel().selectionChanged.connect(self._update_ui)
        self._list.model().rowsInserted.connect(self._update_ui)
        self._list.model().rowsRemoved.connect(self._update_ui)
        delete_action = QtW.QAction(parent=self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self._delete_selected_rows)
        self._list.addAction(delete_action)
        layout.addWidget(self._list, stretch=1)

        # Destination
        self._dest_path_warning_label = components.LabelWithIcon(
            utils.gui.icon('warning_small'),
            '',
            parent=self
        )
        retain_size = self._dest_path_warning_label.sizePolicy()
        retain_size.setRetainSizeWhenHidden(True)
        self._dest_path_warning_label.setSizePolicy(retain_size)
        layout.addWidget(self._dest_path_warning_label)

        dest_layout = QtW.QHBoxLayout()

        dest_layout.addWidget(QtW.QLabel(_t('dialog.batch_move.destination'), parent=self))

        self._destination_input = QtW.QLineEdit(parent=self)
        self._destination_input.textChanged.connect(self._update_ui)
        dest_layout.addWidget(self._destination_input, stretch=1)

        self._choose_destination_button = QtW.QPushButton(utils.gui.icon('directory'), '', parent=self)
        self._choose_destination_button.setToolTip(_t('dialog.batch_move.choose_directory_button.tooltip'))
        self._choose_destination_button.clicked.connect(self._set_destination)
        dest_layout.addWidget(self._choose_destination_button)

        layout.addLayout(dest_layout)

        apply_button_layout = QtW.QHBoxLayout()
        self._apply_button = QtW.QPushButton(
            self.style().standardIcon(QtW.QStyle.SP_DialogApplyButton),
            _t('dialog.batch_move.move_button.label'),
            parent=self
        )
        self._apply_button.setFixedWidth(80)
        self._apply_button.clicked.connect(self._on_move_files)
        apply_button_layout.addWidget(self._apply_button)
        layout.addLayout(apply_button_layout)

        layout.addStretch()

        self.setMinimumSize(350, 220)
        self.setGeometry(0, 0, 350, 280)

        body_layout = QtW.QVBoxLayout()
        scroll = QtW.QScrollArea(parent=self)
        scroll.setWidgetResizable(True)
        w = QtW.QWidget(parent=self)
        w.setLayout(layout)
        scroll.setWidget(w)
        body_layout.addWidget(scroll)

        return body_layout

    def _add_row(self, is_file: bool, path: str):
        icon = utils.gui.icon('image') if is_file else utils.gui.icon('directory')
        item = QtW.QListWidgetItem(icon, path)
        item.setWhatsThis('file' if is_file else 'directory')
        self._list.addItem(item)

    def _delete_selected_rows(self):
        for i in sorted(self._list.selectedIndexes(), key=lambda i: -i.row()):
            self._list.takeItem(i.row())

    def _add_files_or_directories(self, select_files: bool):
        single_selection = not select_files
        selection = self._open_files_chooser(select_files, single_selection)
        if selection:
            if select_files:
                if single_selection:
                    self._add_row(True, selection)
                else:
                    for p in selection:
                        self._add_row(True, p)
            else:
                self._add_row(False, selection)

    def _set_destination(self):
        selection = self._open_files_chooser(select_files=False)
        if selection:
            self._destination_input.setText(selection)

    def _open_files_chooser(self, select_files: bool, single_selection: bool = True):
        if select_files:
            selection = utils.gui.open_file_chooser(
                single_selection=single_selection, mode=utils.gui.FILTER_IMAGES, parent=self)
        else:
            selection = utils.gui.choose_directory(parent=self)
        return selection

    def _update_ui(self):
        list_empty = not self._list.count()
        selected_items = self._list.selectedItems()
        dest_exists = os.path.isdir(self._destination_input.text())
        self._list_warning_label.setVisible(list_empty)
        self._delete_items_button.setDisabled(not selected_items)
        self._clear_list_button.setDisabled(not selected_items)
        if not dest_exists:
            self._dest_path_warning_label.setText(
                _t('dialog.batch_move.destination_empty') if not self._destination_input.text()
                else _t('dialog.batch_move.destination_non_existant')
            )
        self._dest_path_warning_label.setVisible(not dest_exists)
        self._apply_button.setDisabled(not dest_exists or list_empty)

    def _on_move_files(self):
        self._progress_dialog = QtW.QProgressDialog(
            '',
            _t('dialog.common.cancel_button.label'),
            0,
            100,
            parent=self
        )
        self._progress_dialog.setWindowTitle(_t('popup.progress.title'))
        self._progress_dialog.setModal(True)

        elements = []
        for i in range(self._list.count()):
            item = self._list.item(i)
            elements.append((item.text(), item.whatsThis() == 'file'))
        # Put files first, then directories
        elements.sort(key=lambda e: (not e[1], e[0]))
        destination = self._destination_input.text()
        self._thread = _WorkerThread({k: v for k, v in elements}, destination)
        self._thread.progress_signal.connect(self._on_progress_update)
        self._thread.finished.connect(self._on_work_done)
        self._progress_dialog.open(self._thread.cancel)
        self._thread.start()

    def _on_progress_update(self, progress: float, data: typ.Tuple[str, bool], status: int):
        self._progress_dialog.setValue(int(progress * 100))
        status_label = _t('popup.progress.status_label')
        if status == 1:
            status_ = _t('popup.progress.status.success')
        elif status == 2:
            status_ = _t('popup.progress.status.failed')
        else:
            status_ = _t('popup.progress.status.unknown')
        self._progress_dialog.setLabelText(
            f'{progress * 100:.2f} %\n{data[0]}\n{status_label} {status_}'
        )

    def _on_work_done(self):
        self._progress_dialog.cancel()
        if self._thread.failed:
            utils.gui.show_error(self._thread.error, parent=self)
        if self._thread.failed_elements:
            errors = '\n'.join(map(lambda i: i.path, self._thread.failed_elements))
            message = _t('popup.files_move_result_errors.text', errors=errors)
            utils.gui.show_warning(message, _t('popup.files_move_result_errors.title'), parent=self)
        else:
            message = _t('popup.files_move_result_success.text')
            utils.gui.show_info(message, _t('popup.files_move_result_success.title'), parent=self)

        # Remove items that were successfully moved
        for i in reversed(range(self._list.count())):
            if self._list.item(i).text() not in self._thread.failed_elements:
                self._list.takeItem(i)

        self._update_ui()


class _WorkerThread(threads.WorkerThread):
    """Moves the selected files and directories to the selected destination."""

    def __init__(self, elements: typ.Dict[str, bool], destination: str):
        super().__init__()
        self._elements = elements
        self._destination = destination
        self._failed_elements: typ.Dict[str, typ.Tuple[bool, str]] = {}

    def run(self):
        image_dao = data_access.ImageDao(config.CONFIG.database_path)

        total = len(self._elements)
        progress = 0
        for i, (path, is_file) in enumerate(self._elements.items()):
            if self._cancelled:
                break
            self.progress_signal.emit(progress, (path, is_file), self.STATUS_UNKNOWN)
            try:
                shutil.move(path, self._destination)
            except OSError as e:
                self._failed_elements[path] = (is_file, str(e))
                ok = False
            else:  # TODO tester
                try:
                    if is_file:
                        p = image_dao.escape_metatag_plain_value(path)
                        images = image_dao.get_images(queries.query_to_sympy(f'path:"{p}"'))
                        if images:
                            for image in images:
                                new_path = os.path.join(self._destination, image.path.replace(path, ''))
                                image_dao.update_image(image.id, new_path, image.hash)
                    else:
                        p = path
                        if not p.endswith(os.sep):
                            p += os.sep
                        p = image_dao.escape_metatag_plain_value(p)
                        images = image_dao.get_images(queries.query_to_sympy(f'path:"{p}*"'))
                        for image in images:
                            new_path = os.path.join(self._destination, image.path.replace(path, ''))
                            image_dao.update_image(image.id, new_path, image.hash)
                except sqlite3.Error as e:
                    self._failed_elements[path] = (is_file, str(e))
                    ok = False
                else:
                    ok = True

            progress = i / total
            self.progress_signal.emit(progress, (path, is_file),
                                      self.STATUS_SUCCESS if ok else self.STATUS_FAILED)

    @property
    def failed_elements(self) -> typ.Dict[str, typ.Tuple[bool, str]]:
        return self._failed_elements
