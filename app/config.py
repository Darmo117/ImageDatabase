import configparser
import dataclasses as dc
import os

from . import constants, i18n


class ConfigError(ValueError):
    pass


_DEFAULT_LANG_CODE = 'en'
_DEFAULT_DB_PATH = 'library.sqlite3'
_DEFAULT_LOAD_THUMBS = True
_DEFAULT_THUMBS_SIZE = 200
_DEFAULT_THUMBS_LOAD_THRESHOLD = 50


@dc.dataclass
class Config:
    language: i18n.Language = None
    change_to_language: str = None
    database_path: str = _DEFAULT_DB_PATH
    load_thumbnails: bool = _DEFAULT_LOAD_THUMBS
    thumbnail_size: int = _DEFAULT_THUMBS_SIZE
    thumbnail_load_threshold: int = _DEFAULT_THUMBS_LOAD_THRESHOLD
    debug: bool = False


CONFIG = Config()

_UI_SECTION = 'UI'
_DEBUG_KEY = 'Debug'
_LANG_KEY = 'Language'

_DB_SECTION = 'Database'
_FILE_KEY = 'File'

_IMAGES_SECTION = 'Images'
_LOAD_THUMBS_KEY = 'LoadThumbnails'
_THUMB_SIZE_KEY = 'ThumbnailSize'
_THUMB_LOAD_THRESHOLD_KEY = 'ThumbnailLoadThreshold'


def load_config():
    """Loads the configuration file specified in app.constants.CONFIG_FILE.
    If the file does not exist, a default config will be returned.

    :raise ConfigError: If an option is missing or has an illegal value.
    """
    if not i18n.load_languages():
        raise ConfigError(f'could not load languages')

    lang_code = _DEFAULT_LANG_CODE
    if os.path.exists(constants.CONFIG_FILE):
        config_parser = configparser.ConfigParser()
        config_parser.read(constants.CONFIG_FILE)
        try:
            # UI section
            lang_code = config_parser.get(_UI_SECTION, _LANG_KEY, fallback=_DEFAULT_LANG_CODE)
            CONFIG.debug = config_parser.get(_UI_SECTION, _DEBUG_KEY, fallback=False)

            # Images section
            load_thumbs = _to_bool(config_parser.get(_IMAGES_SECTION, _LOAD_THUMBS_KEY,
                                                     fallback=str(_DEFAULT_LOAD_THUMBS)))

            try:
                size = int(config_parser.get(_IMAGES_SECTION, _THUMB_SIZE_KEY, fallback=str(_DEFAULT_THUMBS_SIZE)))
            except ValueError as e:
                raise ConfigError(f'key {_THUMB_SIZE_KEY!r}: {e}')
            if size < constants.MIN_THUMB_SIZE or size > constants.MAX_THUMB_SIZE:
                raise ConfigError(f'illegal thumbnail size {size}px, must be between {constants.MIN_THUMB_SIZE}px '
                                  f'and {constants.MAX_THUMB_SIZE}px')

            try:
                threshold = int(config_parser.get(_IMAGES_SECTION, _THUMB_LOAD_THRESHOLD_KEY,
                                                  fallback=_DEFAULT_THUMBS_LOAD_THRESHOLD))
            except ValueError as e:
                raise ConfigError(f'key {_THUMB_LOAD_THRESHOLD_KEY!r}: {e}')
            if threshold < 0:
                raise ConfigError(f'illegal thumbnail load threshold {threshold}, must be between '
                                  f'{constants.MIN_THUMB_LOAD_THRESHOLD}px and {constants.MAX_THUMB_LOAD_THRESHOLD}px')

            CONFIG.load_thumbnails = load_thumbs
            CONFIG.thumbnail_size = size
            CONFIG.thumbnail_load_threshold = threshold

            # Database section
            CONFIG.database_path = config_parser.get(_DB_SECTION, _FILE_KEY, fallback=_DEFAULT_DB_PATH)
        except ValueError as e:
            raise ConfigError(e)
        except KeyError as e:
            raise ConfigError(f'missing key {e}')

    CONFIG.language = i18n.get_language(lang_code) or i18n.get_language(_DEFAULT_LANG_CODE)
    if not CONFIG.language:
        raise ConfigError('could not load language')


def _to_bool(value: str) -> bool:
    if value.lower() in ['true', '1', 'yes']:
        return True
    elif value.lower() in ['false', '0', 'no']:
        return False
    else:
        raise ConfigError(f'illegal value {repr(value)} for key {repr(_LOAD_THUMBS_KEY)}')


def save_config():
    """Saves the config in the file specified in app.constants.CONFIG_FILE."""
    parser = configparser.ConfigParser(strict=True)
    parser.optionxform = str
    parser[_UI_SECTION] = {
        _LANG_KEY: CONFIG.change_to_language or CONFIG.language.code,
        _DEBUG_KEY: CONFIG.debug,
    }
    parser[_IMAGES_SECTION] = {
        _LOAD_THUMBS_KEY: str(CONFIG.load_thumbnails).lower(),
        _THUMB_SIZE_KEY: CONFIG.thumbnail_size,
        _THUMB_LOAD_THRESHOLD_KEY: CONFIG.thumbnail_load_threshold,
    }
    parser[_DB_SECTION] = {
        _FILE_KEY: CONFIG.database_path,
    }
    with open(constants.CONFIG_FILE, 'w', encoding='UTF-8') as configfile:
        parser.write(configfile)
