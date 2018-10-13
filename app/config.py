import configparser
import os
from dataclasses import dataclass

from . import constants


class ConfigError(ValueError):
    pass


@dataclass
class Config:
    database_path: str = "."
    load_thumbnails: bool = True
    thumbnail_size: int = 200


CONFIG: Config = None

_DB_SECTION = "Database"
_FILE_KEY = "File"
_IMAGES_SECTION = "Images"
_LOAD_THUMBS_KEY = "LoadThumbnails"
_THUMB_SIZE_KEY = "ThumbnailSize"


def load_config():
    """
    Loads the configuration file specified in app.constants.CONFIG_FILE.
    If the file does not exist, a default config will be returned.

    :raise ConfigError: If an option is missing or has an illegal value.
    """
    global CONFIG

    if not os.path.exists(constants.CONFIG_FILE):
        CONFIG = Config()
        return

    config = configparser.ConfigParser()
    config.read(constants.CONFIG_FILE)
    try:
        images_section = config[_IMAGES_SECTION]
        load_t = images_section[_LOAD_THUMBS_KEY]
        if load_t.lower() == "true":
            load = True
        elif load_t.lower() == "false":
            load = False
        else:
            raise ConfigError(f"illegal value {repr(load_t)} for key {repr(_LOAD_THUMBS_KEY)}")
        CONFIG = Config(config[_DB_SECTION][_FILE_KEY], load, int(images_section[_THUMB_SIZE_KEY]))
    except ValueError as e:
        raise ConfigError(e)
    except KeyError as e:
        raise ConfigError(f"missing key {e}")


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
    with open(constants.CONFIG_FILE, "w") as configfile:
        parser.write(configfile)
