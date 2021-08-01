import collections
import dataclasses
import json
import pathlib
import sys
import typing as typ

from . import constants
from .logging import logger


@dataclasses.dataclass(frozen=True)
class Language:
    name: str
    code: str
    _mappings: typ.Mapping[str, str]

    def translate(self, key: str, default: str = None, **kwargs):
        """Translates the given key in this language.

        :param key: The key to translate
        :param default: The default value to return if the specified key does not exist.
        :param kwargs: Keyword arguments to use for formatting.
        :return: The translated string.
        """
        return self._mappings.get(key, default or key).format(**kwargs)

    def __eq__(self, other):
        return isinstance(other, Language) and self.code == other.code


def translate(key: str, default: str = None, **kwargs):
    """Translates the given key in the current language.

    :param key: The key to translate
    :param default: The default value to return if the specified key does not exist.
    :param kwargs: Keyword arguments to use for formatting.
    :return: The translated string.
    """
    from . import config
    return config.CONFIG.language.translate(key, default=default, **kwargs)


def get_language(code: str) -> typ.Optional[Language]:
    return _LANGUAGES.get(code)


def get_languages() -> typ.List[Language]:
    return sorted(_LANGUAGES.values(), key=lambda lang: lang.name)


def load_languages() -> bool:
    for path in constants.LANG_DIR.glob('*'):
        if path.is_file() and path.name.lower().endswith('.json'):
            if res := _get_language_for_file(path):
                _LANGUAGES[res[1]] = res[0]

    return len(_LANGUAGES) != 0


def _get_language_for_file(path: pathlib.Path) -> typ.Optional[typ.Tuple[Language, str]]:
    """Loads the language from the given file.

    :param path: File path.
    :return: A Language object, None if the file could not be found or is improperly formatted.
    """
    mappings = {}
    code = path.stem
    try:
        with path.open(encoding='UTF-8') as f:
            json_object = json.load(f)
        for k, v in _build_mapping(json_object['mappings']).items():
            mappings[k] = v
        return Language(name=json_object['name'], code=code, _mappings=mappings), code
    except (KeyError, FileNotFoundError, json.JSONDecodeError) as e:
        logger.exception(f'could not load language file {path}')
        print(f'could not load language file {path}', file=sys.stderr)
        print(e, file=sys.stderr)
        return None


def _build_mapping(json_object: typ.Mapping[str, typ.Union[str, typ.Mapping]], root: str = None) \
        -> typ.Dict[str, str]:
    """
    Converts a JSON object to a flat key-value mapping.
    This function is recursive.

    :param json_object: The JSON object to flatten.
    :param root: The root to prepend to the keys.
    :return: The flattened mapping.
    :raises ValueError: If one of the values in the JSON object is neither a string or a mapping.
    """
    mapping = {}

    for k, v in json_object.items():
        if root is not None:
            key = f'{root}.{k}'
        else:
            key = k
        if isinstance(v, str):
            mapping[key] = str(v)
        elif isinstance(v, collections.Mapping):
            mapping = dict(mapping, **_build_mapping(v, key))
        else:
            raise ValueError(f'illegal value type "{type(v)}" for translation value')

    return mapping


_MAPPINGS = {}
_LANGUAGES = {}
