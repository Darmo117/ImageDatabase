import typing as typ

import PyQt5.QtWidgets as QtW
from PyQt5.QtCore import Qt

from .dialog_base import Dialog
from ..components import EllipsisLabel
from ... import model, data_access, utils
from ...i18n import translate as _t


class SimilarImagesDialog(Dialog):
    def __init__(self, images: typ.List[typ.Tuple[model.Image, float]], image_dao: data_access.ImageDao,
                 tags_dao: data_access.TagsDao, parent: QtW.QWidget = None):
        self._images = images
        self._index = -1
        super().__init__(parent=parent, title=_t('dialog.similar_images.title'), modal=True, mode=self.OK_CANCEL)
        self._ok_btn.setText(_t('dialog.similar_images.button.copy_tags.label'))
        self._ok_btn.setDisabled(True)
        self._cancel_btn.setText(_t('dialog.similar_images.button.close.label'))
        self._image_dao = image_dao
        self._tags_dao = tags_dao

    def show(self):
        super().show()
        utils.gui.center(self)

    def _init_body(self):
        layout = QtW.QVBoxLayout()

        layout.addWidget(QtW.QLabel(_t('dialog.similar_images.text'), parent=self))

        layout.addSpacing(10)

        grid_layout = QtW.QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setColumnStretch(1, 1)
        label = QtW.QLabel(_t('dialog.similar_images.grid.header.image_path'))
        label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(label, 0, 1)
        label = QtW.QLabel(_t('dialog.similar_images.grid.header.image_size'))
        label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(label, 0, 2)
        label = QtW.QLabel(_t('dialog.similar_images.grid.header.confidence_score'))
        label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(label, 0, 3)

        button_group = QtW.QButtonGroup()
        for i, (image, score) in enumerate(self._images):
            radio_button = QtW.QRadioButton(parent=self)
            radio_button.clicked.connect(self._on_radio_button_clicked)
            radio_button.setWhatsThis(str(i))
            button_group.addButton(radio_button)
            grid_layout.addWidget(radio_button, i + 1, 0)

            label = EllipsisLabel(image.path)
            label.setToolTip(image.path)
            label.setMinimumWidth(80)
            label.setAlignment(Qt.AlignLeft)
            grid_layout.addWidget(label, i + 1, 1)

            image_size = utils.image.image_size(image.path)
            label = QtW.QLabel(f'{image_size[0]}×{image_size[1]}')
            label.setFixedWidth(80)
            label.setAlignment(Qt.AlignCenter)
            grid_layout.addWidget(label, i + 1, 2)

            label = QtW.QLabel(f'{score * 100:.2f} %')
            label.setFixedWidth(80)
            label.setAlignment(Qt.AlignCenter)
            grid_layout.addWidget(label, i + 1, 3)

            button = QtW.QPushButton(_t('dialog.similar_images.grid.open_file_button.label'), parent=self)
            button.setWhatsThis(str(i))
            button.clicked.connect(self._on_open_file_button_clicked)
            button.setFixedWidth(80)
            grid_layout.addWidget(button, i + 1, 4)
        layout.addLayout(grid_layout)

        layout.addStretch(1)

        self.setGeometry(0, 0, 500, self.height())

        return layout

    def _on_radio_button_clicked(self):
        self._index = int(self.sender().whatsThis())
        self._ok_btn.setDisabled(False)

    def _on_open_file_button_clicked(self):
        index = int(self.sender().whatsThis())
        utils.gui.show_file(self._images[index][0].path)

    def get_tags(self) -> typ.Optional[typ.List[model.Tag]]:
        if self._applied and 0 <= self._index < len(self._images):
            return self._image_dao.get_image_tags(self._images[self._index][0].id, self._tags_dao)
        return None
