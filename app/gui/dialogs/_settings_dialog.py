import os
import typing as typ

import PyQt5.QtWidgets as QtW

from app import config, utils, i18n, constants
from app.i18n import translate as _t
from . import _dialog_base
from .. import components


class SettingsDialog(_dialog_base.Dialog):
    """This dialog lets users edit app settings."""

    def __init__(self, parent: typ.Optional[QtW.QWidget] = None):
        self._initial_config = config.CONFIG.copy(replace_by_pending=True)
        super().__init__(parent, _t('dialog.settings.title'), modal=True)
        self._update_ui()

    def _init_body(self) -> typ.Optional[QtW.QLayout]:
        layout = QtW.QVBoxLayout()

        # Database
        db_box = QtW.QGroupBox(_t('dialog.settings.box.database.title'), parent=self)
        db_box_layout = QtW.QGridLayout()

        warning_layout = QtW.QHBoxLayout()
        self._db_path_warning_icon = QtW.QLabel(parent=self)
        self._db_path_warning_icon.setPixmap(utils.gui.icon('warning_small').pixmap(16))
        retain_size = self._db_path_warning_icon.sizePolicy()
        retain_size.setRetainSizeWhenHidden(True)
        warning_layout.addWidget(self._db_path_warning_icon)

        self._db_path_warning_label = QtW.QLabel(_t('dialog.settings.box.database.db_path_warning'), parent=self)
        retain_size = self._db_path_warning_label.sizePolicy()
        retain_size.setRetainSizeWhenHidden(True)
        self._db_path_warning_label.setSizePolicy(retain_size)
        warning_layout.addWidget(self._db_path_warning_label, stretch=1)

        warning_widget = QtW.QWidget(parent=self)
        warning_widget.setLayout(warning_layout)
        warning_layout.setContentsMargins(0, 0, 0, 0)
        db_box_layout.addWidget(warning_widget, 0, 0, 1, 3)

        db_box_layout.addWidget(QtW.QLabel(_t('dialog.settings.box.database.db_path.label')), 1, 0)
        self._db_path_input = QtW.QLineEdit(self._initial_config.database_path, parent=self)
        self._db_path_input.textChanged.connect(self._update_ui)
        db_box_layout.addWidget(self._db_path_input, 1, 1)
        choose_file_button = QtW.QPushButton(utils.gui.icon('choose_db_file'), '', parent=self)
        choose_file_button.setToolTip(_t('dialog.settings.box.database.choose_file_button.tooltip'))
        choose_file_button.clicked.connect(self._open_db_file_chooser)
        db_box_layout.addWidget(choose_file_button, 1, 2)

        db_box.setLayout(db_box_layout)
        layout.addWidget(db_box)

        # Thumbnails
        thumbs_box = QtW.QGroupBox(_t('dialog.settings.box.thumbnails.title'), parent=self)
        thumbs_box_layout = QtW.QGridLayout()

        self._load_thumbs_check = QtW.QCheckBox(
            _t('dialog.settings.box.thumbnails.load_thumbs_button.label'),
            parent=self
        )
        self._load_thumbs_check.setChecked(self._initial_config.load_thumbnails)
        thumbs_box_layout.addWidget(self._load_thumbs_check, 0, 0, 1, 2)

        thumbs_box_layout.addWidget(
            QtW.QLabel(_t('dialog.settings.box.thumbnails.thumbs_size'), parent=self),
            1, 0
        )
        self._thumbs_size_input = components.IntLineEdit(
            constants.MIN_THUMB_SIZE,
            constants.MAX_THUMB_SIZE,
            parent=self
        )
        self._thumbs_size_input.set_value(self._initial_config.thumbnail_size)
        self._thumbs_size_input.textChanged.connect(self._update_ui)
        self._thumbs_size_input.setMaximumWidth(100)
        thumbs_box_layout.addWidget(self._thumbs_size_input, 1, 2)

        thumbs_box_layout.addWidget(
            QtW.QLabel(_t('dialog.settings.box.thumbnails.thumbs_threshold'), parent=self),
            2, 0
        )
        self._thumbs_load_threshold_input = components.IntLineEdit(
            constants.MIN_THUMB_LOAD_THRESHOLD,
            constants.MAX_THUMB_LOAD_THRESHOLD,
            parent=self
        )
        self._thumbs_load_threshold_input.set_value(self._initial_config.thumbnail_load_threshold)
        self._thumbs_load_threshold_input.textChanged.connect(self._update_ui)
        self._thumbs_load_threshold_input.setMaximumWidth(100)
        thumbs_box_layout.addWidget(self._thumbs_load_threshold_input, 2, 2)

        thumbs_box.setLayout(thumbs_box_layout)

        layout.addWidget(thumbs_box)

        # Language
        language_box = QtW.QGroupBox(_t('dialog.settings.box.language.title'), parent=self)
        language_box_layout = QtW.QVBoxLayout()

        language_chooser_layout = QtW.QHBoxLayout()
        language_box_layout.addWidget(QtW.QLabel(_t('dialog.settings.box.language.language'), parent=self))
        self._lang_combo = QtW.QComboBox(parent=self)
        for i, lang in enumerate(i18n.get_languages()):
            self._lang_combo.addItem(lang.name, userData=lang)
            if lang == self._initial_config.language:
                self._lang_combo.setCurrentIndex(i)
        self._lang_combo.currentIndexChanged.connect(self._update_ui)
        language_chooser_layout.addWidget(self._lang_combo)
        language_box_layout.addLayout(language_chooser_layout)

        language_box.setLayout(language_box_layout)
        layout.addWidget(language_box)

        layout.addStretch()

        self.setMinimumSize(300, 300)
        self.setGeometry(0, 0, 400, 400)

        body_layout = QtW.QVBoxLayout()
        scroll = QtW.QScrollArea(parent=self)
        scroll.setWidgetResizable(True)
        w = QtW.QWidget(parent=self)
        w.setLayout(layout)
        scroll.setWidget(w)
        body_layout.addWidget(scroll)

        return body_layout

    def _init_buttons(self) -> typ.List[QtW.QAbstractButton]:
        self._apply_button = QtW.QPushButton(_t('dialog.common.apply_button.label'), parent=self)
        self._apply_button.clicked.connect(self._apply)
        return [self._apply_button]

    def _open_db_file_chooser(self):
        file = utils.gui.open_file_chooser(single_selection=True, mode=utils.gui.FILTER_DB, parent=self)
        if file:
            self._db_path_input.setText(file)

    def _update_ui(self):
        file_exists = self._db_file_exists()
        self._db_path_warning_icon.setVisible(not file_exists)
        self._db_path_warning_label.setVisible(not file_exists)
        valid = self._is_valid()
        self._apply_button.setDisabled(not valid or not self._settings_changed())
        self._ok_btn.setDisabled(not valid)

    def _db_file_exists(self) -> bool:
        return os.path.exists(self._db_path_input.text())

    def _settings_changed(self) -> bool:
        db_path = self._db_path_input.text()
        load_thumbs = self._load_thumbs_check.isChecked()
        thumbs_size = self._thumbs_size_input.value()
        thumbs_load_threshold = self._thumbs_load_threshold_input.value()
        language = self._lang_combo.currentData()
        return ((db_path != self._initial_config.database_path)
                or load_thumbs != self._initial_config.load_thumbnails
                or thumbs_size != self._initial_config.thumbnail_size
                or thumbs_load_threshold != self._initial_config.thumbnail_load_threshold
                or language != self._initial_config.language)

    def _is_valid(self) -> bool:
        return self._db_file_exists()

    def _apply(self) -> bool:
        changed = self._settings_changed()
        db_path = self._db_path_input.text()
        load_thumbs = self._load_thumbs_check.isChecked()
        thumbs_size = self._thumbs_size_input.value()
        thumbs_load_threshold = self._thumbs_load_threshold_input.value()
        language = self._lang_combo.currentData()

        needs_restart = False
        if db_path != self._initial_config.database_path:
            config.CONFIG.database_path = db_path
            needs_restart = True
        config.CONFIG.load_thumbnails = load_thumbs
        config.CONFIG.thumbnail_size = thumbs_size
        config.CONFIG.thumbnail_load_threshold = thumbs_load_threshold
        if language != self._initial_config.language:
            config.CONFIG.language = language
            needs_restart = True

        config.CONFIG.save()

        if needs_restart and changed:
            utils.gui.show_info(_t('popup.app_needs_restart.text'), parent=self)

        self._initial_config = config.CONFIG.copy(replace_by_pending=True)
        self._update_ui()

        return super()._apply()
