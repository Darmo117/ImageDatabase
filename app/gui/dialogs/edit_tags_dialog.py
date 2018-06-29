import re
import typing as typ

import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW
from PyQt5.QtCore import Qt

import app.data_access as da
import app.model as model
import app.utils as utils
import config
from .dialog_base import Dialog


class EditTagsDialog(Dialog):
    """This dialog is used to edit tags and tag types."""
    DISABLED_COLOR = QtG.QColor(200, 200, 200)
    FETCH_COLOR = QtG.QColor(140, 200, 255)
    NORMAL_COLOR = QtG.QColor(255, 255, 255)
    COMBO_ITEM_PATTERN = re.compile(r"^(\d+) - (.+)$")

    def __init__(self, parent: QtW.QWidget = None, editable: bool = True):
        """
        Creates a dialog.

        :param parent: The widget this dialog is attached to.
        :param editable: If true tags and types will be editable.
        """
        self._dao = da.TagsDao(config.DATABASE)
        self._init = False
        self._editable = editable

        title = "Edit Tags" if self._editable else "Tags"
        mode = Dialog.CLOSE if not self._editable else Dialog.OK_CANCEL
        super().__init__(parent=parent, title=title, modal=self._editable, mode=mode)

        self._types_changed_rows = set()
        self._types_added_rows = set()
        self._types_deleted_rows = set()

        self._tags_changed_rows = set()
        self._tags_deleted_rows = set()

        self._dummy_type_id = -1
        self._init = True
        self._valid = True

    # noinspection PyUnresolvedReferences
    def _init_body(self) -> typ.Optional[QtW.QLayout]:
        self.setGeometry(0, 0, 400, 400)

        layout = QtW.QVBoxLayout()

        buttons = QtW.QHBoxLayout()
        buttons.addStretch(1)

        self._add_type_btn = QtW.QPushButton()
        self._add_type_btn.setIcon(QtG.QIcon("app/icons/plus.png"))
        self._add_type_btn.setToolTip("Add type")
        self._add_type_btn.setFixedSize(24, 24)
        self._add_type_btn.setFocusPolicy(Qt.NoFocus)
        self._add_type_btn.clicked.connect(self._add_type)
        buttons.addWidget(self._add_type_btn)

        self._delete_btn = QtW.QPushButton()
        self._delete_btn.setIcon(QtG.QIcon("app/icons/cross.png"))
        self._delete_btn.setToolTip("Delete rows")
        self._delete_btn.setFixedSize(24, 24)
        self._delete_btn.clicked.connect(self._delete_selected_row)
        buttons.addWidget(self._delete_btn)

        if self._editable:
            layout.addLayout(buttons)

        self._tabbed_pane = QtW.QTabWidget()
        self._tabbed_pane.currentChanged.connect(self._tab_changed)
        self._tabbed_pane.addTab(self._init_types_tab(), "Tag Types")
        self._tabbed_pane.addTab(self._init_tags_tab(), "All Tags")
        layout.addWidget(self._tabbed_pane)

        search_layout = QtW.QHBoxLayout()
        self._search_field = QtW.QLineEdit()
        self._search_field.setPlaceholderText("Search tag or type…")
        self._search_field.returnPressed.connect(self._search)
        search_layout.addWidget(self._search_field)

        search_btn = QtW.QPushButton("Search")
        search_btn.clicked.connect(self._search)
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        return layout

    def _init_buttons(self):
        if self._editable:
            self._apply_btn = QtW.QPushButton("Apply")
            # noinspection PyUnresolvedReferences
            self._apply_btn.clicked.connect(self._apply)
            self._apply_btn.setEnabled(False)
            return [self._apply_btn]
        else:
            return []

    # noinspection PyUnresolvedReferences
    def _init_types_tab(self):
        self._types_table = QtW.QTableWidget()
        self._types_table.setColumnCount(4)
        self._types_table.setRowCount(len(model.TagType.SYMBOL_TYPES))
        self._types_table.setColumnWidth(0, 30)
        self._types_table.verticalHeader().setDefaultSectionSize(20)
        self._types_table.horizontalHeader().setStretchLastSection(True)
        self._types_table.setHorizontalHeaderLabels(["ID", "Label", "Symbol"])
        self._types_table.cellChanged.connect(self._types_changed)
        self._types_table.itemSelectionChanged.connect(self._selection_changed)
        if not self._editable:
            self._types_table.setSelectionMode(QtW.QAbstractItemView.SingleSelection)
        else:
            delete_action = QtW.QAction(self)
            delete_action.setShortcut("Delete")
            delete_action.triggered.connect(self._delete_selected_row)
            self._types_table.addAction(delete_action)

        self._types = sorted(model.TagType.SYMBOL_TYPES.values(), key=lambda t: t.label)

        for i, tag_type in enumerate(self._types):
            self._add_type_item(tag_type, i)

        return self._types_table

    # noinspection PyTypeChecker,PyUnresolvedReferences
    def _init_tags_tab(self):
        self._tags_table = QtW.QTableWidget()
        self._tags_table.setColumnCount(4)
        self._tags_table.setColumnWidth(0, 30)
        self._tags_table.verticalHeader().setDefaultSectionSize(20)
        self._tags_table.horizontalHeader().setStretchLastSection(True)
        self._tags_table.setHorizontalHeaderLabels(["ID", "Label", "Type", "Times used"])
        self._tags_table.cellChanged.connect(self._tags_changed)
        self._tags_table.itemSelectionChanged.connect(self._selection_changed)
        if not self._editable:
            self._tags_table.setSelectionMode(QtW.QAbstractItemView.SingleSelection)
        else:
            delete_action = QtW.QAction(self)
            delete_action.setShortcut("Delete")
            delete_action.triggered.connect(self._delete_selected_row)
            self._tags_table.addAction(delete_action)

        self._tags = self._dao.get_all_tags(sort_by_label=True, get_count=True)
        self._tags_table.setRowCount(len(self._tags))
        types = sorted(model.TagType.SYMBOL_TYPES.values(), key=lambda t: t.label)

        if self._tags is not None:
            for i, (tag, count) in enumerate(self._tags):
                id_item = QtW.QTableWidgetItem(str(tag.id))
                id_item.setWhatsThis("id")
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
                id_item.setBackground(EditTagsDialog.DISABLED_COLOR)
                self._tags_table.setItem(i, 0, id_item)

                label_item = QtW.QTableWidgetItem(tag.label)
                label_item.setWhatsThis("label")
                if not self._editable:
                    label_item.setFlags(label_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
                self._tags_table.setItem(i, 1, label_item)

                if self._editable:
                    combo = QtW.QComboBox()
                    combo.currentIndexChanged.connect(self._combo_changed)
                    combo.setWhatsThis("type")
                    combo.setProperty("row", i)
                    combo.addItem("None")
                    for tag_type in types:
                        combo.addItem(EditTagsDialog._to_combo_text(tag_type.id, tag_type.label))
                    if tag.type is not None:
                        combo.setCurrentIndex(
                            combo.findText(EditTagsDialog._to_combo_text(tag.type.id, tag.type.label)))
                    self._tags_table.setCellWidget(i, 2, combo)
                else:
                    type_item = QtW.QTableWidgetItem(tag.type.label if tag.type is not None else "None")
                    type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
                    self._tags_table.setItem(i, 2, type_item)

                number_item = QtW.QTableWidgetItem(str(count))
                number_item.setFlags(number_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
                number_item.setBackground(EditTagsDialog.DISABLED_COLOR)
                self._tags_table.setItem(i, 3, number_item)
        else:
            utils.show_error("Failed to load tags!")
            self._tags = []

        return self._tags_table

    # noinspection PyTypeChecker,PyUnresolvedReferences
    def _add_type_item(self, tag_type, row):
        defined = tag_type is not None
        id_item = QtW.QTableWidgetItem(str(tag_type.id) if defined else str(self._dummy_type_id))
        id_item.setWhatsThis("id")
        id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
        id_item.setBackground(EditTagsDialog.DISABLED_COLOR)
        self._types_table.setItem(row, 0, id_item)

        label_item = QtW.QTableWidgetItem(tag_type.label if defined else "New Type")
        label_item.setWhatsThis("label")
        if not self._editable:
            label_item.setFlags(label_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
        self._types_table.setItem(row, 1, label_item)

        symbol_item = QtW.QTableWidgetItem(tag_type.symbol if defined else "§")
        symbol_item.setWhatsThis("symbol")
        if not self._editable:
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
        self._types_table.setItem(row, 2, symbol_item)

        default_color = QtG.QColor(0, 0, 0)
        bg_color = tag_type.color if defined else default_color
        color = utils.negate(bg_color)
        color_btn = QtW.QPushButton(tag_type.color.name() if defined else default_color.name())
        color_btn.setWhatsThis("color")
        color_btn.setStyleSheet(f"background-color: {bg_color.name()}; color: {color.name()}")
        color_btn.clicked.connect(self._show_color_picker)
        color_btn.setProperty("row", row)
        if not self._editable:
            color_btn.setEnabled(False)
        self._types_table.setCellWidget(row, 3, color_btn)

    def _add_type(self):
        row = self._types_table.rowCount()
        self._types_table.insertRow(row)
        self._init = False
        # noinspection PyTypeChecker
        self._add_type_item(None, row)
        self._types_added_rows.add(row)
        self._init = True
        self._dummy_type_id -= 1

        self._check_integrity()

    def _delete_selected_row(self):
        index = self._tabbed_pane.currentIndex()
        if index == 0:
            self._delete_type()
        elif index == 1:
            self._delete_tag()
        self._check_integrity()

    def _delete_type(self):
        selected_rows = {i.row() for i in self._types_table.selectionModel().selectedRows()}
        if len(selected_rows) > 0:
            choice = utils.show_question("Delete these types?")
            if choice == QtW.QMessageBox.Yes:
                self._types_deleted_rows |= selected_rows - self._types_added_rows
                self._types_changed_rows -= selected_rows
                self._types_added_rows -= selected_rows
                for row in selected_rows:
                    self._types_table.setRowHidden(row, True)
                    ident = self._types_table.item(row, 0).text()
                    label = self._types_table.item(row, 1).text()
                    for tag_row in range(self._tags_table.rowCount()):
                        combo = self._tags_table.cellWidget(tag_row, 2)
                        current_type = EditTagsDialog._label_from_combo(combo.currentText())
                        combo.removeItem(combo.findText(EditTagsDialog._to_combo_text(ident, label)))
                        if current_type == label:
                            combo.setCurrentIndex(0)

    def _delete_tag(self):
        selected_rows = {i.row() for i in self._tags_table.selectionModel().selectedRows()}
        if len(selected_rows) > 0:
            choice = utils.show_question("Delete these tags?")
            if choice == QtW.QMessageBox.Yes:
                self._tags_deleted_rows |= selected_rows
                self._tags_changed_rows -= self._tags_deleted_rows
                for row in selected_rows:
                    self._tags_table.setRowHidden(row, True)

    def _tab_changed(self, index):
        self._add_type_btn.setEnabled(index == 0)
        self._update_delete_btn(index)

    def _selection_changed(self):
        self._update_delete_btn(self._tabbed_pane.currentIndex())

    def _types_changed(self, row, col):
        if self._init and self._editable:
            if col != 3:
                result = EditTagsDialog._check_column(self._types_table, col)
                if result == EditTagsDialog.DUPLICATE:
                    utils.show_error("Value already used! Please choose another.", parent=self)
                if result == EditTagsDialog.EMPTY:
                    utils.show_error("Cell is empty!", parent=self)
                if result == EditTagsDialog.OK and col == 2 and self._check_type_symbol(row) == EditTagsDialog.FORMAT:
                    utils.show_error("Symbol should only be one character long and any character "
                                     'except letters, digits, "_", "+" and "-"!')

            tag_type = self._get_type(row)
            if row not in self._types_added_rows:
                if tag_type != self._types[row]:
                    self._types_changed_rows.add(row)
                elif row in self._types_changed_rows:
                    self._types_changed_rows.remove(row)
            if col == 1:
                for row in range(self._tags_table.rowCount()):
                    if not self._tags_table.isRowHidden(row):
                        combo = self._tags_table.cellWidget(row, 2)
                        for i in range(combo.count()):
                            if combo.itemText(i).startswith(str(tag_type.id) + " "):
                                combo.setItemText(i, EditTagsDialog._to_combo_text(tag_type.id, tag_type.label))
                                break
            self._check_integrity()

    def _tags_changed(self, row, col):
        if self._init and self._editable:
            if col != 2:
                result = EditTagsDialog._check_column(self._tags_table, col)
                if result == EditTagsDialog.DUPLICATE:
                    utils.show_error("Value already used! Please choose another.", parent=self)
                if result == EditTagsDialog.EMPTY:
                    utils.show_error("Cell is empty!", parent=self)
                if result == EditTagsDialog.OK and col == 1 and self._check_tag_format(row) == EditTagsDialog.FORMAT:
                    utils.show_error('Tag label should only be letters, digits or "_"!')

            if row not in self._tags_deleted_rows:
                if self._get_tag(row) != self._tags[row][0]:
                    self._tags_changed_rows.add(row)
                elif row in self._tags_changed_rows:
                    self._tags_changed_rows.remove(row)
            self._check_integrity()

    def _combo_changed(self, _):
        combo = self.sender()
        self._tags_changed(combo.property("row"), 2)

    def _show_color_picker(self):
        color = QtW.QColorDialog.getColor()
        if color.isValid():
            button = self.sender()
            row = button.property("row")
            button.setText(color.name())
            button.setStyleSheet(f"background-color: {color.name()}; color: {utils.negate(color).name()}")
            self._types_changed(row, 3)

    def _update_delete_btn(self, index):
        self._delete_btn.setEnabled(index == 0 and len(self._types_table.selectionModel().selectedRows()) != 0 or
                                    index == 1 and len(self._tags_table.selectionModel().selectedRows()) != 0)

    def _search(self):
        index = self._tabbed_pane.currentIndex()
        text = self._search_field.text().strip()
        if len(text) > 0:
            found = False
            if index == 0:
                for i in range(self._types_table.rowCount()):
                    label_item = self._types_table.item(i, 1)
                    symbol_item = self._types_table.item(i, 2)
                    if label_item.text() == text:
                        self._types_table.setFocus()
                        self._types_table.scrollToItem(label_item)
                        label_item.setBackground(EditTagsDialog.FETCH_COLOR)
                        symbol_item.setBackground(EditTagsDialog.NORMAL_COLOR)
                        found = True
                    elif symbol_item.text() == text:
                        self._types_table.setFocus()
                        self._types_table.scrollToItem(symbol_item)
                        symbol_item.setBackground(EditTagsDialog.FETCH_COLOR)
                        label_item.setBackground(EditTagsDialog.NORMAL_COLOR)
                        found = True
                    else:
                        label_item.setBackground(EditTagsDialog.NORMAL_COLOR)
                        symbol_item.setBackground(EditTagsDialog.NORMAL_COLOR)
            elif index == 1:
                for i in range(self._tags_table.rowCount()):
                    label_item = self._tags_table.item(i, 1)
                    if label_item.text() == text:
                        self._tags_table.setFocus()
                        self._tags_table.scrollToItem(label_item)
                        label_item.setBackground(EditTagsDialog.FETCH_COLOR)
                        found = True
                    else:
                        label_item.setBackground(EditTagsDialog.NORMAL_COLOR)
            if not found:
                utils.show_info("No match found.", parent=self)

    def _is_valid(self):
        return self._valid

    def _apply(self):
        super()._apply()

        ok = True
        update_types = False

        to_keep = []
        for row in self._types_added_rows:
            update_types = True
            res = self._dao.add_type(self._get_type(row))
            if not res:
                to_keep.append(row)
            ok &= res
        self._types_added_rows = to_keep

        to_keep = []
        for row in self._types_deleted_rows:
            update_types = True
            res = self._dao.delete_type(self._get_type(row).id)
            if not res:
                to_keep.append(row)
            ok &= res
        self._types_deleted_rows = to_keep

        to_keep = []
        for row in self._types_changed_rows:
            update_types = True
            res = self._dao.update_type(self._get_type(row))
            if not res:
                to_keep.append(row)
            ok &= res
        self._types_changed_rows = to_keep

        to_keep = []
        for row in self._tags_deleted_rows:
            res = self._dao.delete_tag(self._get_tag(row).id)
            if not res:
                to_keep.append(row)
            ok &= res
        self._tags_deleted_rows = to_keep

        to_keep = []
        for row in self._tags_changed_rows:
            res = self._dao.update_tag(self._get_tag(row))
            if not res:
                to_keep.append(row)
            ok &= res
        self._tags_changed_rows = to_keep

        if update_types:
            model.TagType.init(self._dao.get_all_types())

        if not ok:
            utils.show_error("An error occured! Some changes may not have been saved.")
        else:
            self._apply_btn.setEnabled(False)

        return True

    def _get_type(self, row):
        args = {}

        for i in range(self._types_table.columnCount()):
            cell = self._types_table.item(row, i)
            if cell is None:
                cell = self._types_table.cellWidget(row, i)
            arg = cell.whatsThis()
            if arg == "":
                continue
            if arg == "color":
                args[arg] = cell.palette().button().color()
            else:
                args[arg] = cell.text() if arg != "id" else int(cell.text())

        return model.TagType(**args)

    def _get_tag(self, row):
        args = {}

        for i in range(self._tags_table.columnCount()):
            cell = self._tags_table.item(row, i)
            if cell is None:
                cell = self._tags_table.cellWidget(row, i)
            arg = cell.whatsThis()
            if arg == "":
                continue
            if arg == "type":
                if cell.currentIndex() != 0:
                    ident = EditTagsDialog._id_from_combo(cell.currentText())
                    if ident is not None:
                        args[arg] = model.TagType.from_id(ident)
            else:
                args[arg] = cell.text() if arg != "id" else int(cell.text())

        return model.Tag(**args)

    OK = 0
    DUPLICATE = 1
    EMPTY = 2
    FORMAT = 3

    def _check_tag_format(self, row):
        text = self._tags_table.item(row, 1).text()
        return EditTagsDialog.OK if model.Tag.TAG_PATTERN.match(text) else EditTagsDialog.FORMAT

    def _check_type_symbol(self, row):
        text = self._types_table.item(row, 2).text()
        return EditTagsDialog.OK if model.TagType.SYMBOL_PATTERN.match(text) else EditTagsDialog.FORMAT

    def _check_integrity(self):
        result = EditTagsDialog._check_table_integrity(self._types_table, [1, 2])
        result |= EditTagsDialog._check_table_integrity(self._tags_table, [1])
        self._valid = result == EditTagsDialog.OK
        i = len(self._types_changed_rows) + len(self._types_added_rows) + len(self._types_deleted_rows) + \
            len(self._tags_changed_rows) + len(self._tags_deleted_rows)
        self._apply_btn.setEnabled(i > 0 and self._valid)

    @staticmethod
    def _check_table_integrity(table, columns):
        result = EditTagsDialog.OK
        for col in columns:
            result |= EditTagsDialog._check_column(table, col)
        return result

    @staticmethod
    def _check_column(table, column):
        """
        Checks column's integrity. If a duplicate value is present or a cell is empty, the corresponding error is
        returned.
        """
        for row in range(table.rowCount()):
            if table.isRowHidden(row):
                continue
            if table.item(row, column).text().strip() == "":
                return EditTagsDialog.EMPTY
            label = table.item(row, column).text()
            for r in range(table.rowCount()):
                if table.isRowHidden(r):
                    continue
                if r != row and table.item(r, column).text() == label:
                    return EditTagsDialog.DUPLICATE
        return EditTagsDialog.OK

    @staticmethod
    def _to_combo_text(ident, label):
        return f"{ident} - {label}"

    @staticmethod
    def _label_from_combo(text):
        match = EditTagsDialog.COMBO_ITEM_PATTERN.search(text)
        if match is not None:
            return match.group(2)
        return text

    @staticmethod
    def _id_from_combo(text):
        match = EditTagsDialog.COMBO_ITEM_PATTERN.search(text)
        if match is not None:
            return int(match.group(1))
        return text
