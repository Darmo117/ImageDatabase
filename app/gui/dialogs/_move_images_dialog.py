from __future__ import annotations

import pathlib
import shutil
import typing as typ

import PyQt5.QtWidgets as QtW

from app import utils, data_access, config, model
from app.i18n import translate as _t
from . import _dialog_base
from .. import components, threads


class MoveImagesDialog(_dialog_base.Dialog):
    """This dialog provides tools to apply transformations to images."""

    def __init__(self, images: typ.List[model.Image], parent: typ.Optional[QtW.QWidget] = None):
        self._images = images
        super().__init__(parent=parent, title=_t('dialog.move_images.title'), modal=True,
                         mode=_dialog_base.Dialog.OK_CANCEL)
        self._update_ui()

    def _init_body(self):
        layout = QtW.QVBoxLayout()

        # Destination
        self._dest_path_warning_label = components.LabelWithIcon(
            utils.gui.icon('warning', use_theme=False),
            '',
            parent=self
        )
        retain_size = self._dest_path_warning_label.sizePolicy()
        retain_size.setRetainSizeWhenHidden(True)
        self._dest_path_warning_label.setSizePolicy(retain_size)
        layout.addWidget(self._dest_path_warning_label)

        dest_layout = QtW.QHBoxLayout()

        dest_layout.addWidget(QtW.QLabel(_t('dialog.move_images.destination'), parent=self))

        self._destination_input = QtW.QLineEdit(parent=self)
        self._destination_input.textChanged.connect(self._update_ui)
        dest_layout.addWidget(self._destination_input, stretch=1)

        self._choose_destination_button = QtW.QPushButton(utils.gui.icon('folder'), '', parent=self)
        self._choose_destination_button.setToolTip(_t('dialog.move_images.choose_directory_button.tooltip'))
        self._choose_destination_button.clicked.connect(self._set_destination)
        dest_layout.addWidget(self._choose_destination_button)

        layout.addLayout(dest_layout)

        # Delete empty directories
        self._delete_empty_dirs_check = QtW.QCheckBox(
            _t('dialog.move_images.delete_empty_dirs_button.label'),
            parent=self
        )
        layout.addWidget(self._delete_empty_dirs_check)

        layout.addStretch()

        self.setFixedSize(350, 150)

        return layout

    def _init_buttons(self) -> typ.List[QtW.QAbstractButton]:
        self._ok_btn.setText(_t('dialog.move_images.move_button.label'))

        return []

    def _set_destination(self):
        selection = self._open_files_chooser(select_files=False)
        if selection:
            self._destination_input.setText(str(selection))

    def _open_files_chooser(self, select_files: bool, single_selection: bool = True) \
            -> typ.Optional[typ.Union[typ.List[pathlib.Path], pathlib.Path]]:
        if select_files:
            selection = utils.gui.open_file_chooser(
                single_selection=single_selection, mode=utils.gui.FILTER_IMAGES, parent=self)
        else:
            selection = utils.gui.choose_directory(parent=self)
        return selection

    def _update_ui(self):
        dest = self._destination_input.text()
        dest_exists = dest and pathlib.Path(dest).absolute().is_dir()
        if not dest_exists:
            self._dest_path_warning_label.setText(
                _t('dialog.move_images.destination_empty') if not dest
                else _t('dialog.move_images.destination_non_existant')
            )
        self._dest_path_warning_label.setVisible(not dest_exists)
        self._ok_btn.setDisabled(not dest_exists or not self._images)

    def _on_progress_update(self, progress: float, data: pathlib.Path, status: int):
        self._progress_dialog.setValue(int(progress * 100))
        status_label = _t('popup.progress.status_label')
        if status == 1:
            status_ = _t('popup.progress.status.success')
        elif status == 2:
            status_ = _t('popup.progress.status.failed')
        else:
            status_ = _t('popup.progress.status.unknown')
        self._progress_dialog.setLabelText(
            f'{progress * 100:.2f} %\n{data}\n{status_label} {status_}'
        )

    def _is_valid(self) -> bool:
        dest = self._destination_input.text()
        return dest and pathlib.Path(dest).absolute().is_dir() and self._images

    def _on_work_done(self):
        self._progress_dialog.cancel()
        if self._thread.failed:
            utils.gui.show_error(self._thread.error, parent=self)
        if self._thread.failed_images:
            errors = '\n'.join([str(image.path) for image in self._thread.failed_images])
            utils.gui.show_warning(_t('popup.files_move_result_errors.text', errors=errors), parent=self)
        else:
            message = _t('popup.files_move_result_success.text')
            utils.gui.show_info(message, parent=self)
        if self._thread.failed_deletions:
            errors = '\n'.join([str(path) for path in self._thread.failed_deletions])
            utils.gui.show_warning(_t('popup.directories_deletion_errors.text', errors=errors), parent=self)

        self.close()

    def _apply(self) -> bool:
        self._progress_dialog = QtW.QProgressDialog(
            '',
            _t('dialog.common.cancel_button.label'),
            0,
            100,
            parent=self
        )
        self._progress_dialog.setWindowTitle(_t('popup.progress.title'))
        self._progress_dialog.setMinimumDuration(500)
        self._progress_dialog.setModal(True)

        destination = pathlib.Path(self._destination_input.text()).absolute()
        self._thread = _WorkerThread(self._images, destination, self._delete_empty_dirs_check.isChecked())
        self._thread.progress_signal.connect(self._on_progress_update)
        self._thread.finished.connect(self._on_work_done)
        self._progress_dialog.canceled.connect(self._thread.cancel)
        self._thread.start()

        super()._apply()
        return False


class _WorkerThread(threads.WorkerThread):
    """Moves the selected files and directories to the selected destination."""

    def __init__(self, images: typ.List[model.Image], destination: pathlib.Path, delete_directories_if_empty: bool):
        super().__init__()
        self._images = images
        self._destination = destination
        self._delete_empty_dirs = delete_directories_if_empty
        self._failed_images = []
        self._failed_deletions = []

    def run(self):
        image_dao = data_access.ImageDao(config.CONFIG.database_path)

        dirs = set()
        total = len(self._images)
        progress = 0
        for i, image in enumerate(self._images):
            if self._cancelled:
                break
            self.progress_signal.emit(progress, image.path, self.STATUS_UNKNOWN)
            try:
                shutil.move(str(image.path), self._destination)
            except OSError:
                self._failed_images.append(image)
                ok = False
            else:
                new_path = self._destination / image.path.name
                ok = image_dao.update_image(image.id, new_path, image.hash)
                if not ok:
                    self._failed_images.append(image)
                else:
                    for d in image.path.parents:
                        dirs.add(d)

            progress = i / total
            self.progress_signal.emit(progress, image.path, self.STATUS_SUCCESS if ok else self.STATUS_FAILED)

        if self._delete_empty_dirs:
            stop = False
            while not stop:  # Iterate while there are still empty directories to delete
                nb = len(dirs)
                to_remove = []
                for d in dirs:
                    if d.is_dir() and not next(d.iterdir(), False):
                        try:
                            d.rmdir()
                        except OSError:
                            self._failed_deletions.append(d)
                        to_remove.append(d)
                for d in to_remove:
                    dirs.remove(d)
                stop = nb == len(dirs)

    @property
    def failed_images(self) -> typ.List[model.Image]:
        return self._failed_images

    @property
    def failed_deletions(self) -> typ.List[pathlib.Path]:
        return self._failed_deletions
