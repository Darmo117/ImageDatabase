import os

from PyQt5 import QtWidgets as QtW

import config
from app import utils
from app.data_access import ImageDao
from app.gui.components import Canvas, EllipsisLabel
from app.gui.dialogs.dialog_base import Dialog
from app.model import Image, Tag
from .edit_tags_dialog import EditTagsDialog


class EditImageDialog(Dialog):
    EDIT = 0
    ADD = 1
    REPLACE = 2

    _TITLES = ["Edit", "Add", "Replace"]

    def __init__(self, parent=None, mode=EDIT, show_skip=False):
        if mode != EditImageDialog.EDIT and mode != EditImageDialog.ADD and mode != EditImageDialog.REPLACE:
            raise ValueError("Unknown mode " + str(mode))
        if show_skip and mode == EditImageDialog.REPLACE:
            raise ValueError("Cannot show skip button while on replace mode!")

        self._mode = mode
        self._show_skip = show_skip

        super().__init__(parent=parent, title=EditImageDialog._TITLES[self._mode] + " Image", modal=True)

        self._index = -1
        self._images = []
        self._tags = {}

        self._destination = None
        self._tags_changed = False
        self._image_to_replace = None

        self._dao = ImageDao(config.DATABASE)
        self._tags_dialog = EditTagsDialog(parent=self, editable=False)

    # noinspection PyUnresolvedReferences
    def _init_body(self):
        self.setGeometry(0, 0, 400, 400)

        body = QtW.QVBoxLayout()

        self._canvas = Canvas()
        self._canvas.image = None
        body.addWidget(self._canvas)

        middle = QtW.QHBoxLayout()
        middle.addStretch(1)

        self._dest_label = EllipsisLabel()
        middle.addWidget(self._dest_label)

        text = "Replace with…" if self._mode == EditImageDialog.REPLACE else "Move to…"
        self._dest_btn = QtW.QPushButton(text)
        self._dest_btn.clicked.connect(self._on_dest_button_clicked)
        middle.addWidget(self._dest_btn)
        b = QtW.QPushButton("Tags")
        b.clicked.connect(self._show_tags_dialog)
        middle.addWidget(b)

        body.addLayout(middle)

        self._tags_input = QtW.QTextEdit()
        self._tags_input.textChanged.connect(self._text_changed)
        if self._mode == EditImageDialog.REPLACE:
            self._tags_input.setDisabled(True)
        body.addWidget(self._tags_input)

        self.setMinimumSize(400, 400)

        return body

    def _init_buttons(self):
        if self._mode == EditImageDialog.REPLACE:
            self._ok_btn.setDisabled(True)

        self._skip_btn = None
        if self._show_skip:
            self._skip_btn = QtW.QPushButton("Skip")
            # noinspection PyUnresolvedReferences
            self._skip_btn.clicked.connect(self._next)
            return [self._skip_btn]
        return []

    def _show_tags_dialog(self):
        self._tags_dialog.show()

    def set_images(self, images, tags):
        self._index = 0
        self._images = images
        self._tags = tags
        self._set(self._index)

    def set_image(self, image, tags):
        self._index = 0
        self._images = [image]
        self._tags = {image.id: tags}
        self._set(self._index)

    def _set(self, index):
        image = self._images[index]

        if self._mode == EditImageDialog.REPLACE:
            self._tags_input.setDisabled(False)
        if self._mode != EditImageDialog.ADD:
            self._tags_input.clear()
            tags = []
            if image.id in self._tags:
                tags = [tag.raw_label() for tag in self._tags[image.id]]
            self._tags_input.append(" ".join(tags))
        if self._mode == EditImageDialog.REPLACE:
            self._tags_input.setDisabled(True)
        self._tags_changed = False

        self._canvas.set_image(image.path)

        if self._skip_btn is not None and self._index == len(self._images) - 1:
            self._skip_btn.setDisabled(True)

    def _next(self):
        self._index += 1
        self._set(self._index)

    def _on_dest_button_clicked(self):
        if self._mode == EditImageDialog.REPLACE:
            destination = utils.open_image_chooser(self)
        else:
            destination = utils.choose_directory(self)
        if destination != utils.REJECTED:
            if self._mode == EditImageDialog.REPLACE:
                img = self._images[0]
                if self._image_to_replace is None:
                    self._image_to_replace = img.path
                if self._image_to_replace == destination:
                    utils.show_error("Cannot replace image with itself!", parent=self)
                    return
                self._destination = destination
                self._ok_btn.setDisabled(False)
                self._images[0] = Image(img.id, self._destination)
                self._set(0)
            else:
                self._destination = destination
            self._dest_label.setText("Path: " + self._destination)

    def _text_changed(self):
        self._tags_changed = True

    def _get_tags(self):
        return [Tag.from_string(t) for t in self._tags_input.toPlainText().split()]

    def _is_valid(self):
        try:
            self._get_tags()
            return True
        except ValueError:
            return False

    def _apply(self):
        tags = self._get_tags()
        if len(tags) == 0:
            question = "This image has no tags, you will not be able to request it later. Do you want to continue?"
            choice = utils.show_question(question, title="No tags set", parent=self)
            if choice != QtW.QMessageBox.Yes:
                return False

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
        else:
            text = "Could not apply changes!" if self._mode == EditImageDialog.EDIT else "Could not add image!"
            utils.show_error(text, parent=self)
            close = False

        return close

    def _get_new_path(self, image):
        if self._mode != EditImageDialog.REPLACE and self._destination is not None \
                and os.path.dirname(image.path) != self._destination:
            return utils.slashed(os.path.join(self._destination, os.path.basename(image.path)))
        else:
            return None

    def _add(self, image, tags, new_path):
        ok = True
        if new_path is not None:
            ok = self._move_image(image.path, new_path)
        if ok:
            ok = self._dao.add_image(image.path if new_path is None else new_path, tags)
        return ok

    def _edit(self, image, tags, new_path):
        ok = True
        if new_path is not None:
            ok = self._move_image(image.path, new_path)
            if ok:
                ok = self._dao.update_image_path(image.id, new_path)
        if ok and self._tags_changed:
            ok = self._dao.update_image_tags(image.id, tags)
        return ok

    def _replace(self):
        return self._replace_image(self._images[0].id, self._image_to_replace, self._destination)

    def _move_image(self, path, new_path):
        try:
            os.rename(path, new_path)
            return True
        except FileExistsError:
            utils.show_error("File already exists in destination!", parent=self)
            return False

    def _replace_image(self, id, image_to_replace, new_image):
        """
        Replaces an image by another one in the database. The old image is deleted. The new image will stay in its
        directory.
        :return: True if everything went well
        """
        try:
            os.remove(image_to_replace)
        except FileNotFoundError:
            return False
        return self._dao.update_image_path(id, new_image)

    def closeEvent(self, event):
        self._tags_dialog.close()
        super().closeEvent(event)
