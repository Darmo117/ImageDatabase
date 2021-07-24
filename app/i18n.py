import collections
import json
import typing as typ

from . import constants


def translate(key: str, default: str = None, **kwargs):
    """Translates the given key in the given language.

    :param key: The key to translate
    :param default: The default value to return if the specified key does not exist.
    :param kwargs: Keyword arguments to use for formatting.
    :return: The translated string.
    """
    return _MAPPINGS.get(key, default or key).format(**kwargs)


def load_language(lang_code: str):
    """Loads the mappings for the given language code.

    :param lang_code: Language code.
    """
    global _MAPPINGS
    _MAPPINGS = {}
    with open(constants.LANG_DIR + lang_code + '.json', encoding='UTF-8') as f:
        for k, v in _build_mapping(json.load(f)).items():
            _MAPPINGS[k] = v


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
