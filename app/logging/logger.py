"""This module declares a global Logger object."""

import logging.handlers

from app import constants

_log_dir = constants.ERROR_LOG_FILE.parent
if not _log_dir.exists():
    _log_dir.mkdir()

logging.basicConfig(filename=constants.ERROR_LOG_FILE, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
