import os
import shutil
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

from app import data_access as da, model, utils
from app.i18n import translate as _t
from . import _dialog_base, edit_tags_dialog, similar_images_dialog
from .. import components


class EditImageDialog(_dialog_base.Dialog):
    """This dialog is used to edit information on an image."""
    EDIT = 0
    ADD = 1
    REPLACE = 2

    _TITLES = [
        'dialog.edit_image.title_edit',
        'dialog.edit_image.title_add',
        'dialog.edit_image.title_replace',
    ]

    def __init__(self, image_dao: da.ImageDao, tags_dao: da.TagsDao, parent: QtW.QWidget = None, mode: int = EDIT,
                 show_skip: bool = False):
        """Creates an edition dialog.

        :param image_dao: Image DAO instance.
        :param tags_dao: Tags DAO instance.
        :param parent: The widget this dialog is attached to.
        :param mode: Either EDIT, ADD or REPLACE.
        :param show_skip: If true a 'Skip' button will be added.
        """
        if mode not in (EditImageDialog.EDIT, EditImageDialog.ADD, EditImageDialog.REPLACE):
            raise ValueError(f'unknown mode "{mode}"')
        if show_skip and mode == EditImageDialog.REPLACE:
            raise ValueError('cannot show skip button while on replace mode')

        self._mode = mode
        self._show_skip = show_skip

        self._index = -1
        self._images: typ.List[model.Image] = []
        self._tags: typ.Dict[int, typ.List[model.Tag]] = {}

        super().__init__(parent=parent, title=self._get_title(), modal=True)

        self._destination = None
        self._tags_changed = False
        self._image_to_replace = None
        self._similar_images: typ.List[typ.Tuple[model.Image, float]] = []

        self._image_dao = image_dao
        self._tags_dao = tags_dao
        self._tags_dialog = None

    def _init_body(self) -> QtW.QLayout:
        self.setGeometry(0, 0, 800, 600)
        self.setMinimumSize(800, 600)

        splitter = QtW.QSplitter(parent=self)
        splitter.setOrientation(QtC.Qt.Vertical)

        top_layout = QtW.QVBoxLayout()
        self._image_path_lbl = components.EllipsisLabel('', parent=self)
        top_layout.addWidget(self._image_path_lbl)

        self._canvas = components.Canvas(parent=self)
        top_layout.addWidget(self._canvas)

        top_widget = QtW.QWidget(parent=self)
        top_widget.setLayout(top_layout)

        splitter.addWidget(top_widget)

        bottom_layout = QtW.QVBoxLayout()

        buttons_layout = QtW.QHBoxLayout()

        self._dest_label = components.EllipsisLabel(parent=self)
        buttons_layout.addWidget(self._dest_label)

        buttons_layout.addStretch()

        self._similarities_btn = QtW.QPushButton(
            utils.gui.icon('compare_images'),
            _t('dialog.edit_image.similarities.label'),
            parent=self
        )
        self._similarities_btn.clicked.connect(self._on_show_similarities_dialog)
        self._similarities_btn.hide()  # Show only when relevant
        buttons_layout.addWidget(self._similarities_btn)

        if self._mode == EditImageDialog.REPLACE:
            icon = 'replace_image'
            text = _t('dialog.edit_image.replace_button.label')
        else:
            icon = 'move_to_directory'
            text = _t('dialog.edit_image.move_to_button.label')
        self._dest_btn = QtW.QPushButton(utils.gui.icon(icon), text, parent=self)
        self._dest_btn.clicked.connect(self._on_dest_button_clicked)
        buttons_layout.addWidget(self._dest_btn)
        b = QtW.QPushButton(
            utils.gui.icon('tag'),
            _t('dialog.edit_image.tags_button.label'),
            parent=self
        )
        b.clicked.connect(self._show_tags_dialog)
        buttons_layout.addWidget(b)
        b = QtW.QPushButton(
            utils.gui.icon('image_in_directory'),
            _t('dialog.edit_image.show_directory_button.label'),
            parent=self
        )
        b.clicked.connect(self._open_image_directory)
        buttons_layout.addWidget(b)

        bottom_layout.addLayout(buttons_layout)

        class CustomTextEdit(QtW.QTextEdit):
            """Custom class to catch Ctrl+Enter events."""

            def __init__(self, dialog: EditImageDialog, parent: QtW.QWidget = None):
                super().__init__(parent=parent)
                self._dialog = dialog

            def keyPressEvent(self, event: QtG.QKeyEvent):
                # noinspection PyTypeChecker
                if event.key() in (QtC.Qt.Key_Return, QtC.Qt.Key_Enter) and event.modifiers() & QtC.Qt.ControlModifier:
                    self._dialog._ok_btn.click()
                    event.ignore()
                super().keyPressEvent(event)

        self._tags_input = CustomTextEdit(self, parent=self)
        self._tags_input.textChanged.connect(self._text_changed)
        if self._mode == EditImageDialog.REPLACE:
            self._tags_input.setDisabled(True)
        bottom_layout.addWidget(self._tags_input)

        bottom = QtW.QWidget(parent=self)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom.setLayout(bottom_layout)
        splitter.addWidget(bottom)

        splitter.setSizes([500, 100])

        layout = QtW.QHBoxLayout()
        layout.addWidget(splitter)

        return layout

    def _init_buttons(self) -> typ.List[QtW.QAbstractButton]:
        if self._mode == EditImageDialog.REPLACE:
            self._ok_btn.setDisabled(True)

        self._skip_btn = None
        if self._show_skip:
            self._skip_btn = QtW.QPushButton(
                self.style().standardIcon(QtW.QStyle.SP_ArrowRight),
                _t('dialog.edit_image.skip_button.label'),
                parent=self
            )
            self._skip_btn.clicked.connect(self._next)
            return [self._skip_btn]
        return []

    def _show_tags_dialog(self):
        if self._tags_dialog is None:
            self._tags_dialog = edit_tags_dialog.EditTagsDialog(self._tags_dao, editable=False, parent=self)
        self._tags_dialog.show()

    def _open_image_directory(self):
        """Shows the current image in the system’s file explorer."""
        utils.gui.show_file(self._images[self._index].path)

    def set_images(self, images: typ.List[model.Image], tags: typ.Dict[int, typ.List[model.Tag]]):
        """Sets the images to display. If more than one image are given, they will be displayed one after another when
        the user clicks on 'OK' or 'Skip'.

        :param images: The images to display.
        :param tags: The tags for each image.
        """
        self._index = 0
        self._images = sorted(images)
        self._tags = tags
        self._set(self._index)

    def set_image(self, image, tags):
        """Sets the image to display.

        :param image: The image to display.
        :param tags: The image’s tags.
        """
        self.set_images([image], {image.id: tags})

    def _set(self, index: int):
        """Sets the current image."""
        image = self._images[index]

        self._image_path_lbl.setText(image.path)
        self._image_path_lbl.setToolTip(image.path)

        if self._mode == EditImageDialog.REPLACE:
            self._tags_input.setDisabled(False)
        if self._mode != EditImageDialog.ADD:
            tags = []
            if image.id in self._tags:
                tags = self._tags[image.id]
            self._set_tags(tags)
        if self._mode == EditImageDialog.REPLACE:
            self._tags_input.setDisabled(True)
        self._tags_changed = False

        self._canvas.set_image(image.path)

        similar_images = self._image_dao.get_similar_images(image.path)
        self._similar_images = [(image, score) for image, _, score, same_path in similar_images if not same_path]
        if self._similar_images:
            self._similarities_btn.show()
        else:
            self._similarities_btn.hide()

        if self._index == len(self._images) - 1:
            if self._skip_btn:
                self._skip_btn.setDisabled(True)
            self._ok_btn.setText(_t('dialog.edit_image.finish_button.label'))
        elif self._skip_btn:
            self._ok_btn.setText(_t('dialog.edit_image.apply_next_button.label'))

        self.setWindowTitle(self._get_title())

    def _set_tags(self, tags: typ.List[model.Tag]):
        self._tags_input.setText(' '.join(sorted([tag.raw_label() for tag in tags])))

    def _next(self):
        """Goes to the next image."""
        self._index += 1
        self._set(self._index)

    def _on_show_similarities_dialog(self):
        dialog = similar_images_dialog.SimilarImagesDialog(self._similar_images, self._image_dao, self._tags_dao,
                                                           parent=self)
        dialog.set_on_close_action(self._on_similarities_dialog_closed)
        dialog.show()

    def _on_similarities_dialog_closed(self, dialog: similar_images_dialog.SimilarImagesDialog):
        self._set_tags(dialog.get_tags())

    def _on_dest_button_clicked(self):
        """Opens a directory chooser then sets the destination path to the one selected if any."""
        if self._mode == EditImageDialog.REPLACE:
            destination = utils.gui.open_file_chooser(single_selection=True, mode=utils.gui.FILTER_IMAGES, parent=self)
        else:
            destination = utils.gui.choose_directory(parent=self)
        if destination is not None:
            if self._mode == EditImageDialog.REPLACE:
                img = self._images[0]
                if self._image_to_replace is None:
                    self._image_to_replace = img.path
                if self._image_to_replace == destination:
                    utils.gui.show_error(_t('dialog.edit_image.error.replace_self'), parent=self)
                    return
                self._destination = destination
                self._ok_btn.setDisabled(False)
                self._images[0] = model.Image(id=img.id, path=self._destination, hash=img.hash)
                self._set(0)
            else:
                self._destination = destination
            key = 'target_image' if self._mode == EditImageDialog.REPLACE else 'target_path'
            self._dest_label.setText(_t('dialog.edit_image.' + key, path=self._destination))
            self._dest_label.setToolTip(self._destination)

    def _text_changed(self):
        self._tags_changed = True

    def _get_tags(self) -> typ.List[model.Tag]:
        return [self._tags_dao.create_tag_from_string(t) for t in self._tags_input.toPlainText().split()]

    def _ensure_no_compound_tags(self) -> bool:
        for tag in self._tags_input.toPlainText().split():
            t = tag if tag[0].isalnum() or tag[0] == '_' else tag[1:]
            if self._tags_dao.get_tag_class(t) == model.CompoundTag:
                return False
        return True

    def _get_error(self) -> typ.Optional[str]:
        try:
            tags = self._get_tags()
            if len(tags) == 0:
                return _t('dialog.edit_image.error.no_tags')
            if not self._ensure_no_compound_tags():
                return _t('dialog.edit_image.error.compound_tags_disallowed')
            return None
        except ValueError:
            return _t('dialog.edit_image.error.invalid_tag_format')

    def _is_valid(self) -> bool:
        return self._get_error() is None

    def _apply(self) -> bool:
        tags = self._get_tags()

        image = self._images[self._index]
        new_path = self._get_new_path(image)

        if self._mode == EditImageDialog.ADD:
            ok = self._add(image, tags, new_path)
        elif self._mode == EditImageDialog.EDIT:
            ok = self._edit(image, tags, new_path)
        else:
            ok = self._replace()

        if ok:
            close = self._index == len(self._images) - 1
            if not close:
                self._next()
            super()._apply()
        else:
            if self._mode == EditImageDialog.EDIT:
                text = _t('dialog.edit_image.error.changes_not_applied')
            else:
                text = _t('dialog.edit_image.error.image_not_added')
            utils.gui.show_error(text, parent=self)
            close = False

        return close

    def _get_new_path(self, image: model.Image) -> typ.Optional[str]:
        """Returns the new image path. It is obtained by appending the image name to the destination path.

        :param image: The image to move.
        :return: The new path.
        """
        if self._mode != EditImageDialog.REPLACE and self._destination is not None \
                and os.path.dirname(image.path) != self._destination:
            return utils.gui.slashed(os.path.join(self._destination, os.path.basename(image.path)))
        else:
            return None

    def _add(self, image: model.Image, tags: typ.List[model.Tag], new_path: typ.Optional[str]) -> bool:
        """Adds an image to the database.

        :param image: The image to add.
        :param tags: Image’s tags.
        :param new_path: If present the image will be moved in this directory.
        :return: True if everything went well.
        """
        ok = self._image_dao.add_image(image.path if new_path is None else new_path, tags)
        if new_path is not None and ok:
            ok = self._move_image(image.path, new_path)
        return ok

    def _edit(self, image: model.Image, tags: typ.List[model.Tag], new_path: typ.Optional[str]) -> bool:
        """Edits an image from the database.

        :param image: The image to edit.
        :param tags: Image’s tags.
        :param new_path: If present the image will be moved in this directory.
        :return: True if everything went well.
        """
        if self._tags_changed:
            ok = self._image_dao.update_image_tags(image.id, tags)
        else:
            ok = True
        if ok and new_path is not None:
            ok = self._image_dao.update_image_path(image.id, new_path)
            if ok:
                ok = self._move_image(image.path, new_path)
        return ok

    def _replace(self) -> bool:
        """Replaces an image by another one. The old image is deleted. The new image will stay in its directory.

        :return: True if everything went well.
        """
        try:
            os.remove(self._image_to_replace)
        except OSError:
            return False
        else:
            ok = self._image_dao.update_image_path(self._images[0].id, self._destination)
            return ok

    def _move_image(self, path: str, new_path: str) -> bool:
        """Moves an image to a specific directory.

        :param path: Image’s path.
        :param new_path: Path to the new directory.
        :return: True if the image was moved.
        """
        try:
            shutil.move(path, new_path)
        except shutil.Error:
            utils.gui.show_error(_t('dialog.edit_image.error.file_already_exists'), parent=self)
            return False
        else:
            return True

    def _get_title(self) -> str:
        return _t(self._TITLES[self._mode], index=self._index + 1, total=len(self._images))

    def closeEvent(self, event: QtG.QCloseEvent):
        if self._tags_dialog is not None:
            self._tags_dialog.close()
        super().closeEvent(event)
