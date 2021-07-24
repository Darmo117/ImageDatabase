import configparser
import dataclasses as dc
import os

from . import constants, i18n


class ConfigError(ValueError):
    pass


@dc.dataclass
class Config:
    lang_code: str = 'en'
    database_path: str = 'library.sqlite3'
    load_thumbnails: bool = True
    thumbnail_size: int = 200
    thumbnail_load_threshold: int = 50


CONFIG = Config()

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
    if os.path.exists(constants.CONFIG_FILE):
        config_parser = configparser.ConfigParser()
        config_parser.read(constants.CONFIG_FILE)
        try:
            images_section = config_parser[_IMAGES_SECTION]
            load_thumbs = _to_bool(images_section[_LOAD_THUMBS_KEY])

            try:
                size = int(images_section.get(_THUMB_SIZE_KEY, '200'))
            except ValueError as e:
                raise ConfigError(f'key {_THUMB_SIZE_KEY!r}: {e}')
            if size < constants.MIN_THUMB_SIZE or size > constants.MAX_THUMB_SIZE:
                raise ConfigError(f'illegal thumbnail size {size}px, must be between {constants.MIN_THUMB_SIZE}px '
                                  f'and {constants.MAX_THUMB_SIZE}px')

            try:
                threshold = int(images_section.get(_THUMB_LOAD_THRESHOLD_KEY, '50'))
            except ValueError as e:
                raise ConfigError(f'key {_THUMB_LOAD_THRESHOLD_KEY!r}: {e}')
            if threshold < 0:
                raise ConfigError(f'illegal thumbnail load threshold {threshold}, must be between '
                                  f'{constants.MIN_THUMB_LOAD_THRESHOLD}px and {constants.MAX_THUMB_LOAD_THRESHOLD}px')

            CONFIG.database_path = config_parser[_DB_SECTION][_FILE_KEY]
            CONFIG.load_thumbnails = load_thumbs
            CONFIG.thumbnail_size = size
            CONFIG.thumbnail_load_threshold = threshold
        except ValueError as e:
            raise ConfigError(e)
        except KeyError as e:
            raise ConfigError(f'missing key {e}')

    i18n.load_language(CONFIG.lang_code)


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
    parser[_DB_SECTION] = {
        _FILE_KEY: CONFIG.database_path,
    }
    parser[_IMAGES_SECTION] = {
        _LOAD_THUMBS_KEY: str(CONFIG.load_thumbnails).lower(),
        _THUMB_SIZE_KEY: CONFIG.thumbnail_size,
        _THUMB_LOAD_THRESHOLD_KEY: CONFIG.thumbnail_load_threshold,
    }
    with open(constants.CONFIG_FILE, 'w', encoding='UTF-8') as configfile:
        parser.write(configfile)
