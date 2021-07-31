from __future__ import annotations

import dataclasses
import re
import typing as typ

import PyQt5.QtWidgets as QtW

from app import data_access, queries, config, utils, model
from app.i18n import translate as _t
from . import _dialog_base
from .. import threads


class OperationsDialog(_dialog_base.Dialog):
    """This dialog provides tools to apply transformations to images."""

    def __init__(self, state: OperationsDialog.FormState = None, parent: typ.Optional[QtW.QWidget] = None):
        self._state = state.copy() if state else self.State()
        super().__init__(parent=parent, title=_t('dialog.perform_operations.title'), modal=True,
                         mode=_dialog_base.Dialog.CLOSE)
        self._update_ui()

    def _init_body(self):
        layout = QtW.QVBoxLayout()

        image_paths_box = QtW.QGroupBox(_t('dialog.perform_operations.box.image_paths.title'), parent=self)
        image_paths_layout = QtW.QGridLayout()
        image_paths_box.setLayout(image_paths_layout)

        warning_label = QtW.QLabel(_t('dialog.perform_operations.box.image_paths.description'), parent=self)
        warning_label.setWordWrap(True)
        image_paths_layout.addWidget(warning_label, 0, 0, 1, 2)

        image_paths_layout.addWidget(
            QtW.QLabel(_t('dialog.perform_operations.box.image_paths.regex'), parent=self), 1, 0)
        self._regex_input = QtW.QLineEdit(self._state.regex, parent=self)
        self._regex_input.textChanged.connect(self._update_ui)
        image_paths_layout.addWidget(self._regex_input, 1, 1)

        image_paths_layout.addWidget(
            QtW.QLabel(_t('dialog.perform_operations.box.image_paths.replacement'), parent=self), 2, 0)
        self._replacement_input = QtW.QLineEdit(self._state.replacement, parent=self)
        self._replacement_input.textChanged.connect(self._update_ui)
        image_paths_layout.addWidget(self._replacement_input, 2, 1)

        apply_layout = QtW.QHBoxLayout()
        apply_layout.setContentsMargins(0, 0, 0, 0)
        w = QtW.QWidget(parent=self)
        self._apply_button = QtW.QPushButton(
            self.style().standardIcon(QtW.QStyle.SP_DialogApplyButton),
            _t('dialog.common.apply_button.label'),
            parent=self
        )
        self._apply_button.setFixedWidth(80)
        self._apply_button.clicked.connect(self._on_apply_transformation)
        apply_layout.addWidget(self._apply_button)
        w.setLayout(apply_layout)
        image_paths_layout.addWidget(w, 3, 0, 1, 2)

        layout.addWidget(image_paths_box)

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

    def _update_ui(self):
        self._apply_button.setDisabled(not self._regex_input.text())
        self._state.regex = self._regex_input.text()
        self._state.replacement = self._replacement_input.text()

    def _on_apply_transformation(self):
        self._progress_dialog = QtW.QProgressDialog(
            '',
            _t('dialog.common.cancel_button.label'),
            0,
            100,
            parent=self
        )
        self._progress_dialog.setWindowTitle(_t('popup.progress.title'))
        self._progress_dialog.setModal(True)

        regex = self._regex_input.text()
        replacement = self._replacement_input.text()
        self._thread = _WorkerThread(regex, replacement)
        self._thread.progress_signal.connect(self._on_progress_update)
        self._thread.finished.connect(self._on_work_done)
        self._progress_dialog.open(self._thread.cancel)
        self._thread.start()

    def _on_progress_update(self, progress: float, data: typ.Tuple[str, str], status: int):
        self._progress_dialog.setValue(int(progress * 100))
        status_label = _t('popup.progress.status_label')
        if status == 1:
            status_ = _t('popup.progress.status.success')
        elif status == 2:
            status_ = _t('popup.progress.status.failed')
        else:
            status_ = _t('popup.progress.status.unknown')
        old_path, new_path = data
        self._progress_dialog.setLabelText(
            f'{progress * 100:.2f} %\n{old_path}\n→ {new_path}\n{status_label} {status_}'
        )

    def _on_work_done(self):
        self._progress_dialog.cancel()
        if self._thread.failed:
            utils.gui.show_error(self._thread.error, parent=self)
        elif self._thread.failed_images:
            errors = '\n'.join(map(lambda i: i.path, self._thread.failed_images))
            message = _t('popup.operation_result_errors.text', affected=self._thread.affected, errors=errors)
            utils.gui.show_warning(message, _t('popup.operation_result_errors.title'), parent=self)
        else:
            message = _t('popup.operation_result_success.text', affected=self._thread.affected)
            utils.gui.show_info(message, _t('popup.operation_result_success.title'), parent=self)

        self._update_ui()

    @property
    def state(self) -> OperationsDialog.FormState:
        return self._state.copy()

    @dataclasses.dataclass
    class State:
        regex: str = ''
        replacement: str = ''

        def copy(self) -> OperationsDialog.State:
            return OperationsDialog.State(
                regex=self.regex,
                replacement=self.replacement
            )


class _WorkerThread(threads.WorkerThread):
    """Applies the given replacement of every images whose path match the given regex."""

    def __init__(self, regex: str, replacement: str):
        """Creates a worker thread for a query.

        :param regex: The filter regex.
        :param replacement: The replacement string.
        """
        super().__init__()
        self._regex = regex
        self._replacement = replacement
        self._affected = 0
        self._failed_images: typ.List[model.Image] = []

    def run(self):
        image_dao = data_access.ImageDao(config.CONFIG.database_path)
        try:
            regex = self._regex.replace('/', r'\/')
            query = queries.query_to_sympy(f'path:/{regex}/', simplify=False)
        except ValueError as e:
            self._error = str(e)
            return

        images = image_dao.get_images(query)
        if images is None:
            self._error = _t('thread.search.error.image_loading_error')
        else:
            total = len(images)
            progress = 0
            for i, image in enumerate(images):
                if self._cancelled:
                    break
                new_path = re.sub(self._regex, self._replacement, image.path)
                self.progress_signal.emit(progress, (image.path, new_path), self.STATUS_UNKNOWN)
                new_hash = utils.image.get_hash(new_path)
                ok = image_dao.update_image(image.id, new_path, new_hash)
                if ok:
                    self._affected += 1
                else:
                    self._failed_images.append(image)
                progress = i / total
                self.progress_signal.emit(progress, (image.path, new_path),
                                          self.STATUS_SUCCESS if ok else self.STATUS_FAILED)

    @property
    def failed_images(self) -> typ.List[model.Image]:
        return self._failed_images

    @property
    def affected(self) -> int:
        return self._affected
