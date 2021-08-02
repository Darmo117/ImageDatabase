import typing as typ

import PyQt5.QtWidgets as QtW
from PyQt5.QtCore import Qt

from app import model, data_access, utils
from app.i18n import translate as _t
from . import _dialog_base
from .. import components


class SimilarImagesDialog(_dialog_base.Dialog):
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

    def _init_body(self):
        layout = QtW.QVBoxLayout()

        label = QtW.QLabel(_t('dialog.similar_images.text'), parent=self)
        label.setWordWrap(True)
        layout.addWidget(label)

        layout.addSpacing(10)

        grid_layout = QtW.QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setColumnStretch(1, 1)
        label = QtW.QLabel(_t('dialog.similar_images.grid.header.image_path'), parent=self)
        label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(label, 0, 1)
        label = QtW.QLabel(_t('dialog.similar_images.grid.header.image_size'), parent=self)
        label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(label, 0, 2)
        label = QtW.QLabel(_t('dialog.similar_images.grid.header.confidence_score'), parent=self)
        label.setAlignment(Qt.AlignCenter)
        grid_layout.addWidget(label, 0, 3)

        button_group = QtW.QButtonGroup(parent=self)
        for i, (image, score) in enumerate(self._images):
            radio_button = QtW.QRadioButton(parent=self)
            radio_button.clicked.connect(self._on_radio_button_clicked)
            radio_button.setWhatsThis(str(i))
            button_group.addButton(radio_button, id=i)
            grid_layout.addWidget(radio_button, i + 1, 0)

            label = components.EllipsisLabel(str(image.path), parent=self)
            # Click on associated radio button when label is clicked
            label.set_on_click(lambda this: button_group.button(int(this.whatsThis())).click())
            label.setToolTip(str(image.path))
            label.setMinimumWidth(80)
            label.setAlignment(Qt.AlignLeft)
            label.setWhatsThis(str(i))
            grid_layout.addWidget(label, i + 1, 1)

            image_size = utils.image.image_size(image.path)
            label = QtW.QLabel(f'{image_size[0]}×{image_size[1]}', parent=self)
            label.setFixedWidth(80)
            label.setAlignment(Qt.AlignCenter)
            grid_layout.addWidget(label, i + 1, 2)

            label = QtW.QLabel(f'{score * 100:.2f} %', parent=self)
            label.setFixedWidth(80)
            label.setAlignment(Qt.AlignCenter)
            grid_layout.addWidget(label, i + 1, 3)

            button = QtW.QPushButton(
                utils.gui.icon('folder-open'),
                _t('dialog.similar_images.grid.open_file_button.label'),
                parent=self
            )
            button.setWhatsThis(str(i))
            button.clicked.connect(self._on_open_file_button_clicked)
            button.setFixedWidth(80)
            grid_layout.addWidget(button, i + 1, 4)

        wrapper_layout = QtW.QVBoxLayout()
        wrapper_layout.addLayout(grid_layout)
        wrapper_layout.addStretch()

        scroll = QtW.QScrollArea(parent=self)
        scroll.setWidgetResizable(True)
        w = QtW.QWidget(parent=self)
        w.setLayout(wrapper_layout)
        scroll.setWidget(w)
        layout.addWidget(scroll)

        self.setMinimumSize(500, 200)
        self.setGeometry(0, 0, 500, 200)

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
