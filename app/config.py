from __future__ import annotations

import configparser
import pathlib
import typing as typ

from . import constants, i18n, logging


class ConfigError(ValueError):
    pass


_DEFAULT_LANG_CODE = 'en'
_DEFAULT_DB_PATH = pathlib.Path('library.sqlite3')
_DEFAULT_LOAD_THUMBS = True
_DEFAULT_THUMBS_SIZE = 200
_DEFAULT_THUMBS_LOAD_THRESHOLD = 50
_DEFAULT_DEBUG = False


class Config:
    def __init__(
            self,
            language: i18n.Language,
            database_path: pathlib.Path,
            load_thumbnails: bool,
            thumbnail_size: int,
            thumbnail_load_threshold: int,
            debug: bool, ):
        """Creates a new configuration object.

        :param language: App’s UI language.
        :param database_path: Path to database file.
        :param load_thumbnails: Whether to load thumbnails when querying images.
        :param thumbnail_size: Thumbnails maximum width and height.
        :param thumbnail_load_threshold: Limit above which thumbnails will
            automatically be disabled to avoid memory issues.
        :param debug: Whether to load the app in debug mode. Set to True if you have issues with file dialogs.
        """
        self._language = language
        self._language_pending = None
        self._database_path = database_path
        self._database_path_pending = None
        self.load_thumbnails = load_thumbnails
        self.thumbnail_size = thumbnail_size
        self.thumbnail_load_threshold = thumbnail_load_threshold
        self._debug = debug

    @property
    def language(self) -> i18n.Language:
        return self._language

    @language.setter
    def language(self, value: i18n.Language):
        self._language_pending = value

    @property
    def language_pending(self) -> typ.Optional[i18n.Language]:
        return self._language_pending

    @property
    def database_path(self) -> pathlib.Path:
        return self._database_path

    @database_path.setter
    def database_path(self, value: pathlib.Path):
        self._database_path_pending = value

    @property
    def database_path_pending(self) -> typ.Optional[pathlib.Path]:
        return self._database_path_pending

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def app_needs_restart(self) -> bool:
        """Whether the application needs to be restarted to apply some changes."""
        return self._language_pending or self._database_path_pending

    def copy(self, replace_by_pending: bool = False) -> Config:
        """Returns a copy of this Config object."""
        return Config(
            language=self.language if not replace_by_pending or not self.language_pending else self.language_pending,
            database_path=(self.database_path if not replace_by_pending or not self.database_path_pending
                           else self.database_path_pending),
            load_thumbnails=self.load_thumbnails,
            thumbnail_size=self.thumbnail_size,
            thumbnail_load_threshold=self.thumbnail_load_threshold,
            debug=self.debug,
        )

    def save(self):
        """Saves the config to the file specified in app.constants.CONFIG_FILE."""
        parser = configparser.ConfigParser(strict=True)
        parser.optionxform = str

        parser[_UI_SECTION] = {
            _LANG_KEY: self.language_pending.code if self.language_pending else self.language.code,
        }
        if self.debug:  # Write only if True
            parser[_UI_SECTION][_DEBUG_KEY] = 'true'
        parser[_IMAGES_SECTION] = {
            _LOAD_THUMBS_KEY: str(self.load_thumbnails).lower(),
            _THUMB_SIZE_KEY: self.thumbnail_size,
            _THUMB_LOAD_THRESHOLD_KEY: self.thumbnail_load_threshold,
        }
        parser[_DB_SECTION] = {
            _FILE_KEY: str(self.database_path_pending or self.database_path),
        }

        try:
            with constants.CONFIG_FILE.open(mode='w', encoding='UTF-8') as configfile:
                parser.write(configfile)
        except IOError as e:
            logging.logger.exception(e)
            return False
        else:
            return True


# noinspection PyTypeChecker
CONFIG: Config = None

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
    global CONFIG

    if not i18n.load_languages():
        raise ConfigError(f'could not load languages')

    lang_code = _DEFAULT_LANG_CODE
    database_path = _DEFAULT_DB_PATH
    load_thumbs = _DEFAULT_LOAD_THUMBS
    thumbs_size = _DEFAULT_THUMBS_SIZE
    thumbs_load_threshold = _DEFAULT_THUMBS_LOAD_THRESHOLD
    debug = _DEFAULT_DEBUG

    config_file_exists = constants.CONFIG_FILE.is_file()

    if config_file_exists:
        config_parser = configparser.ConfigParser()
        config_parser.read(constants.CONFIG_FILE)
        try:
            # UI section
            lang_code = config_parser.get(_UI_SECTION, _LANG_KEY, fallback=_DEFAULT_LANG_CODE)
            debug = _to_bool(config_parser.get(_UI_SECTION, _DEBUG_KEY, fallback=_DEFAULT_DEBUG))

            # Images section
            load_thumbs = _to_bool(config_parser.get(_IMAGES_SECTION, _LOAD_THUMBS_KEY,
                                                     fallback=str(_DEFAULT_LOAD_THUMBS)))

            try:
                thumbs_size = int(
                    config_parser.get(_IMAGES_SECTION, _THUMB_SIZE_KEY, fallback=str(_DEFAULT_THUMBS_SIZE)))
            except ValueError as e:
                raise ConfigError(f'key {_THUMB_SIZE_KEY!r}: {e}')
            if thumbs_size < constants.MIN_THUMB_SIZE or thumbs_size > constants.MAX_THUMB_SIZE:
                raise ConfigError(
                    f'illegal thumbnail size {thumbs_size}px, must be between {constants.MIN_THUMB_SIZE}px '
                    f'and {constants.MAX_THUMB_SIZE}px')

            try:
                thumbs_load_threshold = int(config_parser.get(_IMAGES_SECTION, _THUMB_LOAD_THRESHOLD_KEY,
                                                              fallback=_DEFAULT_THUMBS_LOAD_THRESHOLD))
            except ValueError as e:
                raise ConfigError(f'key {_THUMB_LOAD_THRESHOLD_KEY!r}: {e}')
            if thumbs_load_threshold < 0:
                raise ConfigError(f'illegal thumbnail load threshold {thumbs_load_threshold}, must be between '
                                  f'{constants.MIN_THUMB_LOAD_THRESHOLD}px and {constants.MAX_THUMB_LOAD_THRESHOLD}px')

            # Database section
            database_path = pathlib.Path(config_parser.get(_DB_SECTION, _FILE_KEY, fallback=_DEFAULT_DB_PATH))
        except ValueError as e:
            raise ConfigError(e)
        except KeyError as e:
            raise ConfigError(f'missing key {e}')

    language = i18n.get_language(lang_code) or i18n.get_language(_DEFAULT_LANG_CODE)
    if not language:
        raise ConfigError('could not load language')

    CONFIG = Config(language, database_path, load_thumbs, thumbs_size, thumbs_load_threshold, debug)

    if not config_file_exists:
        CONFIG.save()


def _to_bool(value: typ.Union[str, bool]) -> bool:
    if isinstance(value, bool):
        return value
    elif value.lower() in ['true', '1', 'yes']:
        return True
    elif value.lower() in ['false', '0', 'no']:
        return False
    else:
        raise ConfigError(f'illegal value {repr(value)} for key {repr(_LOAD_THUMBS_KEY)}')
