import sqlite3
import typing as typ

import PyQt5.QtCore as QtC
import PyQt5.QtGui as QtG
import PyQt5.QtWidgets as QtW

from app import config, data_access
from app.i18n import translate as _t
from . import _dialog_base
from .. import components


class CommandLineDialog(_dialog_base.Dialog):
    """A simple command line interface to interact with the database."""

    def __init__(self, parent: QtW.QWidget = None):
        super().__init__(
            parent=parent,
            title=_t('dialog.command_line.title'),
            modal=True,
            mode=_dialog_base.Dialog.CLOSE
        )
        # noinspection PyProtectedMember
        self._connection = data_access.ImageDao(config.CONFIG.database_path)._connection
        self._command_line.setFocus()
        self._disable_closing = False

        self._column_names = None
        self._results = None
        self._results_offset = None
        self._results_total = None

    def _init_body(self) -> QtW.QLayout:
        self.setMinimumSize(500, 300)

        layout = QtW.QVBoxLayout()

        self._command_line = components.CommandLineWidget(parent=self)
        self._command_line.set_input_callback(self._on_input)
        self._command_line.set_input_placeholder(_t('dialog.command_line.query_input.placeholder'))
        layout.addWidget(self._command_line)

        return layout

    def _on_input(self, input_: str):
        if self._results:
            if input_.upper() == 'Y':
                self._print_results()
            elif input_.upper() == 'N':
                self._column_names = None
                self._results = None
            else:
                self._command_line.print(_t('SQL_console.display_more'))
        else:
            cursor = self._connection.cursor()
            try:
                cursor.execute(input_)
            except sqlite3.Error as e:
                self._command_line.print_error(_t('SQL_console.error'))
                self._command_line.print_error(e)
                cursor.close()
            else:
                if input_.lower().startswith('select'):
                    results = cursor.fetchall()
                    if cursor.description is not None:
                        column_names = tuple(desc[0] for desc in cursor.description)
                    else:
                        column_names = ()
                    self._column_names = column_names
                    self._results = results
                    self._results_offset = 0
                    self._results_total = len(results)
                    self._print_results()
                else:
                    self._command_line.print(_t('SQL_console.affected_rows', row_count=cursor.rowcount))
                cursor.close()

    def _print_results(self):
        results = self._results[self._results_offset:]
        if len(results) == 0:
            self._command_line.print(_t('SQL_console.no_results'))
        else:
            limit = 20
            i = 0
            rows = []
            for result in results:
                if i % limit == 0:
                    if i > 0:
                        self._print_rows(rows, self._column_names)
                        rows.clear()
                        self._command_line.print(_t('SQL_console.display_more'))
                        self._results_offset += i
                        break
                    upper_bound = min(self._results_offset + i + limit, self._results_total)
                    self._command_line.print(_t('SQL_console.results', start=self._results_offset + i + 1,
                                                end=upper_bound, total=self._results_total))
                rows.append(tuple(map(repr, result)))
                i += 1
            else:
                self._print_rows(rows, self._column_names)
                self._results = None

    def _print_rows(self, rows: list[tuple[str, ...]], column_names: typ.Sequence[str]):
        """Prints rows in a table.

        :param rows: List of rows.
        :param column_names: Names of each column.
        """
        columns = list(zip(*([column_names] + rows)))
        column_sizes = [max([len(str(v)) for v in col]) for col in columns]
        self._command_line.print(*[str(v).ljust(column_sizes[i]) for i, v in enumerate(column_names)], sep=' | ')
        self._command_line.print(*['-' * size for size in column_sizes], sep='-+-')
        for i, row in enumerate(rows):
            self._command_line.print(*[str(v).ljust(column_sizes[i]) for i, v in enumerate(row)], sep=' | ')

    def keyPressEvent(self, event: QtG.QKeyEvent):
        if event.key() in [QtC.Qt.Key_Return, QtC.Qt.Key_Enter] and self.focusWidget() != self._ok_btn:
            self._disable_closing = True
        super().keyPressEvent(event)

    def _on_ok_clicked(self):
        if self._disable_closing:
            self._disable_closing = False
        else:
            super()._on_ok_clicked()
