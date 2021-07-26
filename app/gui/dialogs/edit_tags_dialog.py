import typing as typ

import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW
from PyQt5.QtCore import Qt

from .dialog_base import Dialog
from .tabs import TagsTab, TagTypesTab, CompoundTagsTab
from ... import config, data_access as da, model, utils, constants
from ...i18n import translate as _t


class EditTagsDialog(Dialog):
    """This dialog is used to edit tags and tag types."""
    _TAG_TYPES_TAB = 0
    _COMPOUND_TAGS_TAB = 1
    _TAGS_TAB = 2

    def __init__(self, parent: typ.Optional[QtW.QWidget] = None, editable: bool = True):
        """Creates a dialog.

        :param parent: The widget this dialog is attached to.
        :param editable: If true tags and types will be editable.
        """
        self._init = False
        self._editable = editable

        def type_cell_changed(row: int, col: int, _):
            if col == 1:
                for tab in self._tabs[1:]:
                    tag_type = self._tabs[self._TAG_TYPES_TAB].get_value(row)
                    if tag_type is not None:
                        tab.update_type_label(tag_type)
            self._check_integrity()

        def types_deleted(deleted_types: typ.List[model.TagType]):
            for tab in self._tabs[1:]:
                tab.delete_types(deleted_types)

        dao = da.TagsDao(config.CONFIG.database_path)
        self._tabs = (
            TagTypesTab(self, dao, self._editable, selection_changed=self._selection_changed,
                        cell_changed=type_cell_changed, rows_deleted=types_deleted),
            CompoundTagsTab(self, dao, self._editable, selection_changed=self._selection_changed,
                            cell_changed=self._check_integrity, rows_deleted=self._check_integrity),
            TagsTab(self, dao, self._editable, selection_changed=self._selection_changed,
                    cell_changed=self._check_integrity, rows_deleted=self._check_integrity)
        )

        title = _t('dialog.edit_tags.title_edit') if self._editable else _t('dialog.edit_tags.title_readonly')
        mode = self.CLOSE if not self._editable else self.OK_CANCEL
        super().__init__(parent=parent, title=title, modal=self._editable, mode=mode)
        self._valid = True

    def _init_body(self) -> QtW.QLayout:
        self.setGeometry(0, 0, 400, 400)

        layout = QtW.QVBoxLayout()

        buttons = QtW.QHBoxLayout()
        buttons.addStretch(1)

        self._add_row_btn = QtW.QPushButton()
        self._add_row_btn.setIcon(QtG.QIcon(constants.ICONS_DIR + 'plus.png'))
        self._add_row_btn.setToolTip(_t('dialog.edit_tags.add_item_button.tooltip'))
        self._add_row_btn.setFixedSize(24, 24)
        self._add_row_btn.setFocusPolicy(Qt.NoFocus)
        self._add_row_btn.clicked.connect(self._add_row)
        buttons.addWidget(self._add_row_btn)

        self._delete_row_btn = QtW.QPushButton()
        self._delete_row_btn.setIcon(QtG.QIcon(constants.ICONS_DIR + 'cross.png'))
        self._delete_row_btn.setToolTip(_t('dialog.edit_tags.delete_items_button.tooltip'))
        self._delete_row_btn.setFixedSize(24, 24)
        self._delete_row_btn.setFocusPolicy(Qt.NoFocus)
        self._delete_row_btn.clicked.connect(self._delete_selected_row)
        buttons.addWidget(self._delete_row_btn)

        if self._editable:
            layout.addLayout(buttons)

        self._tabbed_pane = QtW.QTabWidget()
        self._tabbed_pane.currentChanged.connect(self._tab_changed)
        self._init_tabs()
        layout.addWidget(self._tabbed_pane)

        search_layout = QtW.QHBoxLayout()
        self._search_field = QtW.QLineEdit()
        self._search_field.setPlaceholderText(_t('dialog.edit_tags.search_field.placeholder'))
        self._search_field.returnPressed.connect(self._search)
        search_layout.addWidget(self._search_field)

        search_btn = QtW.QPushButton(_t('dialog.edit_tags.search_button.label'))
        search_btn.clicked.connect(self._search)
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        return layout

    def _init_buttons(self) -> typ.List[QtW.QAbstractButton]:
        if self._editable:
            self._ok_btn.setEnabled(False)
            self._apply_btn = QtW.QPushButton(_t('dialog.edit_tags.apply_button.label'))
            self._apply_btn.clicked.connect(self._apply)
            self._apply_btn.setEnabled(False)
            return [self._apply_btn]
        else:
            return []

    def _init_tabs(self):
        self._tabbed_pane.clear()
        for tab in self._tabs:
            tab.init()
            self._tabbed_pane.addTab(tab.table, tab.title)

    def _add_row(self):
        self._tabs[self._tabbed_pane.currentIndex()].add_row()
        self._check_integrity()

    def _delete_selected_row(self):
        self._tabs[self._tabbed_pane.currentIndex()].delete_selected_rows()
        self._check_integrity()

    def _tab_changed(self, index: int):
        self._add_row_btn.setEnabled(self._tabs[index].addable)
        self._update_delete_row_btn(index)

    def _selection_changed(self):
        self._update_delete_row_btn(self._tabbed_pane.currentIndex())

    def _update_delete_row_btn(self, index: int):
        tab = self._tabs[index]
        self._delete_row_btn.setEnabled(tab.deletable and tab.selected_rows_number != 0)

    def _search(self):
        text = self._search_field.text().strip()
        if len(text) > 0:
            found = self._tabs[self._tabbed_pane.currentIndex()].search(text)
            if not found:
                utils.show_info(_t('dialog.edit_tags.no_match'), parent=self)

    def _is_valid(self) -> bool:
        return self._valid

    def _apply(self) -> bool:
        ok = all(map(lambda t: t.apply(), self._tabs))
        if not ok:
            utils.show_error(_t('dialog.edit_tags.error.saving'), parent=self)
        else:
            self._apply_btn.setEnabled(False)
            super()._apply()
            self._init_tabs()

        return True

    def _check_integrity(self, *_):
        """Checks the integrity of all tables. Parameters are ignored, they are here only to conform to the Tab class
        constructor.
        """
        self._valid = all(map(lambda t: t.check_integrity(), self._tabs))
        edited_rows_nb = sum(map(lambda t: t.modified_rows_number, self._tabs))
        self._apply_btn.setEnabled(edited_rows_nb > 0 and self._valid)
        self._ok_btn.setEnabled(self._valid)
