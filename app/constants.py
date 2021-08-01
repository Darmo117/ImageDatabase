import pathlib

APP_NAME = 'Image Library'
VERSION = '4.0'
DB_SETUP_FILE = pathlib.Path('app/data_access/setup.sql').absolute()
CONFIG_FILE = pathlib.Path('config.ini').absolute()
ERROR_LOG_FILE = pathlib.Path('logs/errors.log').absolute()
ICONS_DIR = pathlib.Path('app/assets/icons/').absolute()
LANG_DIR = pathlib.Path('app/assets/lang/').absolute()
GRAMMAR_FILE = pathlib.Path('app/queries/grammar.lark').absolute()
IMAGE_FILE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'bmp', 'gif']
MIN_THUMB_SIZE = 50
MAX_THUMB_SIZE = 2000
MIN_THUMB_LOAD_THRESHOLD = 0
MAX_THUMB_LOAD_THRESHOLD = 1000
