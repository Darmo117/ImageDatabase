import logging.handlers
import os

import config

if not os.path.exists(os.path.dirname(config.ERROR_LOG_FILE)):
    os.mkdir(os.path.dirname(config.ERROR_LOG_FILE))

logging.basicConfig(filename=config.ERROR_LOG_FILE, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
