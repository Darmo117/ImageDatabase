import configparser
import os
import dataclasses as dc

from . import constants


class ConfigError(ValueError):
    pass


@dc.dataclass
class Config:
    database_path: str = '.'
    load_thumbnails: bool = True
    thumbnail_size: int = 200


CONFIG: Config = Config()

_DB_SECTION = 'Database'
_FILE_KEY = 'File'
_IMAGES_SECTION = 'Images'
_LOAD_THUMBS_KEY = 'LoadThumbnails'
_THUMB_SIZE_KEY = 'ThumbnailSize'


def load_config():
    """
    Loads the configuration file specified in app.constants.CONFIG_FILE.
    If the file does not exist, a default config will be returned.

    :raise ConfigError: If an option is missing or has an illegal value.
    """
    if not os.path.exists(constants.CONFIG_FILE):
        return

    config_parser = configparser.ConfigParser()
    config_parser.read(constants.CONFIG_FILE)
    try:
        images_section = config_parser[_IMAGES_SECTION]
        load_thumbs = _to_bool(images_section[_LOAD_THUMBS_KEY])
        size = int(images_section[_THUMB_SIZE_KEY])
        if size < constants.MIN_THUMB_SIZE or size > constants.MAX_THUMB_SIZE:
            raise ConfigError(f'illegal thumbnail size {size}px, must be between {constants.MIN_THUMB_SIZE}px '
                              f'and {constants.MAX_THUMB_SIZE}px')
        CONFIG.database_path = config_parser[_DB_SECTION][_FILE_KEY]
        CONFIG.load_thumbnails = load_thumbs
        CONFIG.thumbnail_size = size
    except ValueError as e:
        raise ConfigError(e)
    except KeyError as e:
        raise ConfigError(f'missing key {e}')


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
    }
    with open(constants.CONFIG_FILE, 'w', encoding='UTF-8') as configfile:
        parser.write(configfile)
