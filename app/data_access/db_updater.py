import os
import pathlib
import shutil
import sqlite3
import typing as typ

import PyQt5.QtWidgets as QtW

from ._migrations import migrations
from .. import config, constants, gui, utils
from ..i18n import translate as _t


def update_database_if_needed() -> typ.Tuple[typ.Optional[bool], typ.Optional[str]]:
    """Updates the database if it needs to be."""
    db_file = config.CONFIG.database_path
    setup = not db_file.exists()
    connection = sqlite3.connect(str(db_file))
    connection.isolation_level = None

    if setup:
        with constants.DB_SETUP_FILE.open(encoding='UTF-8') as f:
            connection.executescript(f.read())

    try:
        cursor = connection.execute('SELECT db_version, app_version FROM version')
    except sqlite3.OperationalError:
        db_version = 0
        app_version = '3.1'
    else:
        db_version, app_version = cursor.fetchone()
        cursor.close()
    connection.close()

    if db_version == len(migrations):  # DB up to date, return now
        return True, None

    if not utils.gui.show_question(_t('popup.update_needed.text')):  # Update cancelled
        return None, None

    progress_dialog = QtW.QProgressDialog('', _t('dialog.common.cancel_button.label'), 0, 100)
    progress_dialog.setWindowTitle(_t('popup.database_update.title'))

    def update_progress(progress: float, data: str, _):
        progress_dialog.setValue(int(progress * 100))
        progress_dialog.setLabelText(data)

    thread = _UpdateThread(setup, db_file, db_version, app_version)
    thread.progress_signal.connect(update_progress)
    progress_dialog.canceled.connect(thread.cancel)
    thread.finished.connect(progress_dialog.cancel)
    thread.start()
    progress_dialog.exec_()

    if thread.error:
        message = thread.error
        status = False
    elif thread.cancelled:
        message = _t('popup.update_cancelled.text')
        status = None
    else:
        message = _t('popup.database_updated.text')
        status = True

    return status, message


class _UpdateThread(gui.threads.WorkerThread):
    def __init__(self, setup: bool, db_file: pathlib.Path, previous_db_version: str, previous_app_version: str):
        super().__init__()
        self._setup = setup
        self._db_file = db_file
        self._db_version = previous_db_version
        self._app_version = previous_app_version

    def run(self):
        connection = sqlite3.connect(str(self._db_file))
        connection.isolation_level = None
        # Apply all migrations starting from the DB’s version all the way up to the current version
        for i, migration in enumerate(migrations[self._db_version:]):
            if self.cancelled:
                break
            self.progress_signal.emit(0, '', self.STATUS_UNKNOWN)
            if i == 0 and not self._setup:
                name, ext = os.path.splitext(self._db_file.name)
                shutil.copy(self._db_file, self._db_file.parent / f'{name}-old_{self._app_version}{ext}')
            migration.migrate(connection, self)
