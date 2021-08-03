from __future__ import annotations

import dataclasses
import pathlib
import re
import typing as typ

import PyQt5.QtWidgets as QtW

from app import data_access, queries, config, utils, model
from app.i18n import translate as _t
from . import _dialog_base, _progress_dialog
from .. import threads, components


class OperationsDialog(_dialog_base.Dialog):
    """This dialog provides tools to apply transformations to images."""

    def __init__(self, tags: typ.Iterable[str], state: OperationsDialog.FormState = None,
                 parent: typ.Optional[QtW.QWidget] = None):
        self._state = state.copy() if state else self.State()
        self._tags = tags
        super().__init__(parent=parent, title=_t('dialog.perform_operations.title'), modal=True,
                         mode=_dialog_base.Dialog.CLOSE)
        self._update_ui()

    def _init_body(self):
        layout = QtW.QVBoxLayout()

        # Path pattern replacer
        image_paths_box = QtW.QGroupBox(_t('dialog.perform_operations.box.image_paths.title'), parent=self)
        image_paths_layout = QtW.QGridLayout()
        image_paths_box.setLayout(image_paths_layout)

        warning_label = QtW.QLabel(_t('dialog.perform_operations.box.image_paths.description'), parent=self)
        warning_label.setWordWrap(True)
        image_paths_layout.addWidget(warning_label, 0, 0, 1, 2)

        image_paths_layout.addWidget(
            QtW.QLabel(_t('dialog.perform_operations.box.image_paths.regex'), parent=self), 1, 0)
        self._regex_input = components.TranslatedLineEdit(self._state.regex, parent=self)
        self._regex_input.textChanged.connect(self._update_ui)
        image_paths_layout.addWidget(self._regex_input, 1, 1)

        image_paths_layout.addWidget(
            QtW.QLabel(_t('dialog.perform_operations.box.image_paths.replacement'), parent=self), 2, 0)
        self._replacement_input = components.TranslatedLineEdit(self._state.replacement, parent=self)
        self._replacement_input.textChanged.connect(self._update_ui)
        image_paths_layout.addWidget(self._replacement_input, 2, 1)

        apply_layout = QtW.QHBoxLayout()
        apply_layout.setContentsMargins(0, 0, 0, 0)
        apply_layout.addStretch()
        w = QtW.QWidget(parent=self)
        self._paths_apply_button = QtW.QPushButton(
            self.style().standardIcon(QtW.QStyle.SP_DialogApplyButton),
            _t('dialog.common.apply_button.label'),
            parent=self
        )
        self._paths_apply_button.setFixedWidth(80)
        self._paths_apply_button.clicked.connect(lambda: self._replace(_WorkerThread.PATHS))
        apply_layout.addWidget(self._paths_apply_button)
        apply_layout.addStretch()
        w.setLayout(apply_layout)
        image_paths_layout.addWidget(w, 3, 0, 1, 2)

        layout.addWidget(image_paths_box)

        # Tags replacer
        tags_repl_box = QtW.QGroupBox(_t('dialog.perform_operations.box.tags_replacer.title'), parent=self)
        tags_repl_layout = QtW.QGridLayout()
        tags_repl_box.setLayout(tags_repl_layout)

        tags_repl_layout.addWidget(QtW.QLabel(_t('dialog.perform_operations.box.tags_replacer.tag_to_replace')), 0, 0)
        self._tag_to_replace_input = components.AutoCompleteLineEdit(parent=self)
        self._tag_to_replace_input.setText(self._state.tag_to_replace)
        self._tag_to_replace_input.set_completer_model(self._tags)
        self._tag_to_replace_input.textChanged.connect(self._update_ui)
        tags_repl_layout.addWidget(self._tag_to_replace_input, 0, 1)

        tags_repl_layout.addWidget(QtW.QLabel(_t('dialog.perform_operations.box.tags_replacer.replacement_tag')), 1, 0)
        self._replacement_tag_input = components.AutoCompleteLineEdit(parent=self)
        self._replacement_tag_input.setText(self._state.replacement_tag)
        self._replacement_tag_input.set_completer_model(self._tags)
        self._replacement_tag_input.textChanged.connect(self._update_ui)
        tags_repl_layout.addWidget(self._replacement_tag_input, 1, 1)

        self._delete_tag_after = QtW.QCheckBox(
            _t('dialog.perform_operations.box.tags_replacer.delete_tag_after'),
            parent=self
        )
        self._delete_tag_after.setChecked(self._state.delete_tag_after_replacement)
        self._delete_tag_after.clicked.connect(self._update_ui)
        tags_repl_layout.addWidget(self._delete_tag_after, 2, 0, 1, 2)

        apply_layout = QtW.QHBoxLayout()
        apply_layout.addStretch()
        apply_layout.setContentsMargins(0, 0, 0, 0)
        w = QtW.QWidget(parent=self)
        self._tags_apply_button = QtW.QPushButton(
            self.style().standardIcon(QtW.QStyle.SP_DialogApplyButton),
            _t('dialog.perform_operations.box.tags_replacer.replace_tag_button.label'),
            parent=self
        )
        self._tags_apply_button.clicked.connect(lambda: self._replace(_WorkerThread.TAGS))
        apply_layout.addWidget(self._tags_apply_button)
        apply_layout.addStretch()
        w.setLayout(apply_layout)
        tags_repl_layout.addWidget(w, 3, 0, 1, 2)

        layout.addWidget(tags_repl_box)

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
        regex = self._regex_input.text()
        tag_to_repl = self._tag_to_replace_input.text()
        repl_tag = self._replacement_tag_input.text()
        self._paths_apply_button.setDisabled(not regex)
        self._tags_apply_button.setDisabled(tag_to_repl not in self._tags or tag_to_repl == repl_tag
                                            or (repl_tag != '' and repl_tag not in self._tags))
        self._state.regex = regex
        self._state.replacement = self._replacement_input.text()
        self._state.tag_to_replace = tag_to_repl
        self._state.replacement_tag = repl_tag
        self._state.delete_tag_after_replacement = self._delete_tag_after.isChecked()

    def _replace(self, mode: int):
        self._progress_dialog = _progress_dialog.ProgressDialog(parent=self)

        if mode == _WorkerThread.PATHS:
            to_replace = self._regex_input.text()
            replacement = self._replacement_input.text()
        elif mode == _WorkerThread.TAGS:
            to_replace = self._tag_to_replace_input.text()
            replacement = self._replacement_tag_input.text()
        else:
            to_replace = None
            replacement = None

        if to_replace:
            delete_tag_after = mode == _WorkerThread.TAGS and self._delete_tag_after.isChecked()
            self._thread = _WorkerThread(to_replace, replacement, mode, delete_tag_after=delete_tag_after)
            self._thread.progress_signal.connect(self._on_progress_update)
            self._thread.finished.connect(self._on_work_done)
            self._progress_dialog.canceled.connect(self._thread.cancel)
            self._thread.start()

    def _on_progress_update(self, progress: float, data: tuple, status: int):
        progress *= 100
        self._progress_dialog.setValue(int(progress))
        status_label = _t('popup.progress.status_label')
        if status == 1:
            status_ = _t('popup.progress.status.success')
        elif status == 2:
            status_ = _t('popup.progress.status.failed')
        else:
            status_ = _t('popup.progress.status.unknown')
        mode = data[0]
        if mode == _WorkerThread.PATHS:
            old_path, new_path = data[1:]
            self._progress_dialog.setLabelText(
                f'{progress:.2f} %\n{old_path}\n→ {new_path}\n{status_label} {status_}'
            )
        elif mode == _WorkerThread.TAGS:
            image_path = data[1]
            self._progress_dialog.setLabelText(
                f'{progress:.2f} %\n{image_path}\n{status_label} {status_}'
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

        tag_to_replace: str = ''
        replacement_tag: str = ''
        delete_tag_after_replacement: bool = True

        def copy(self) -> OperationsDialog.State:
            return OperationsDialog.State(
                regex=self.regex,
                replacement=self.replacement,
                tag_to_replace=self.tag_to_replace,
                replacement_tag=self.replacement_tag,
                delete_tag_after_replacement=self.delete_tag_after_replacement
            )


class _WorkerThread(threads.WorkerThread):
    """Applies the given replacement of every images whose path match the given regex."""

    PATHS = 0
    TAGS = 1

    def __init__(self, to_replace: str, replacement: str, mode: int, delete_tag_after: bool = False):
        """Creates a worker thread for a query.

        :param to_replace: The text to replace.
        :param replacement: The replacement string.
        :param mode: Replacement mode.
        """
        super().__init__()
        self._mode = mode
        self._to_replace = to_replace
        self._replacement = replacement
        self._delete_tag_after = delete_tag_after
        self._affected = 0
        self._failed_images: typ.List[model.Image] = []

    def run(self):
        if self._mode == self.PATHS:
            self._replace_paths()
        elif self._mode == self.TAGS:
            self._replace_tags()

    def _replace_paths(self):
        image_dao = data_access.ImageDao(config.CONFIG.database_path)
        try:
            regex = self._to_replace.replace('/', r'\/')
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
                # Replace but keep absolute path
                new_path = pathlib.Path(re.sub(self._to_replace, self._replacement, str(image.path))).absolute()
                self.progress_signal.emit(progress, (self._mode, image.path, new_path), self.STATUS_UNKNOWN)
                new_hash = utils.image.get_hash(new_path)
                ok = image_dao.update_image(image.id, new_path, new_hash)
                if ok:
                    self._affected += 1
                else:
                    self._failed_images.append(image)
                progress = i / total
                self.progress_signal.emit(progress, (self._mode, image.path, new_path),
                                          self.STATUS_SUCCESS if ok else self.STATUS_FAILED)

    def _replace_tags(self):
        image_dao = data_access.ImageDao(config.CONFIG.database_path)
        tags_dao = data_access.TagsDao(config.CONFIG.database_path)
        try:
            query = queries.query_to_sympy(self._to_replace, simplify=False)
        except ValueError as e:
            self._error = str(e)
            return

        images = image_dao.get_images(query)
        if images is None:
            self._error = _t('thread.search.error.image_loading_error')
        else:
            tag_to_replace = tags_dao.get_tag_from_label(self._to_replace)
            replacement_tag = tags_dao.get_tag_from_label(self._replacement) if self._replacement else None
            if not tag_to_replace:
                self._error = _t('thread.perform_operations.error.non_existent_tag', label=self._to_replace)
            elif self._replacement and not replacement_tag:
                self._error = _t('thread.perform_operations.error.non_existent_tag', label=self._replacement)
            elif isinstance(tag_to_replace, model.CompoundTag):
                self._error = _t('thread.perform_operations.error.compound_tag', label=self._to_replace)
            elif isinstance(replacement_tag, model.CompoundTag):
                self._error = _t('thread.perform_operations.error.compound_tag', label=self._replacement)
            else:
                total = len(images)
                progress = 0
                for i, image in enumerate(images):
                    if self._cancelled:
                        break
                    self.progress_signal.emit(progress, (self._mode, image.path), self.STATUS_UNKNOWN)
                    tags = [tag for tag in image_dao.get_image_tags(image.id, tags_dao)
                            if tag.label not in (self._to_replace, self._replacement)]
                    if replacement_tag:
                        tags.append(replacement_tag)
                    ok = image_dao.update_image_tags(image.id, tags)
                    if ok:
                        self._affected += 1
                    else:
                        self._failed_images.append(image)
                    progress = i / total
                    self.progress_signal.emit(progress, (self._mode, image.path),
                                              self.STATUS_SUCCESS if ok else self.STATUS_FAILED)

                if self._delete_tag_after and not self._failed_images:
                    tags_dao.delete_tag(tag_to_replace.id)

    @property
    def failed_images(self) -> typ.List[model.Image]:
        return self._failed_images

    @property
    def affected(self) -> int:
        return self._affected
