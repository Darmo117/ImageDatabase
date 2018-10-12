"""This module declares a global Logger object."""

import logging.handlers
import os

from app import constants

if not os.path.exists(os.path.dirname(constants.ERROR_LOG_FILE)):
    os.mkdir(os.path.dirname(constants.ERROR_LOG_FILE))

logging.basicConfig(filename=constants.ERROR_LOG_FILE, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
