"""Utility functions to handle files."""
import os
import pathlib
import typing as typ

from app import constants


def accept_image_files(filenames: typ.Sequence[typ.Union[str, pathlib.Path]]) -> bool:
    """Indicates whether the given files have valid image extensions."""
    return all(map(accept_image_file, filenames))


def accept_image_file(filename: typ.Union[str, pathlib.Path]) -> bool:
    """Indicates whether the given file has a valid image extension."""
    return get_extension(filename) in constants.IMAGE_FILE_EXTENSIONS


def get_extension(filename: typ.Union[str, pathlib.Path], keep_dot: bool = False) -> str:
    """Returns the extension of the given file.

    :param filename: File’s name.
    :param keep_dot: Whether to return keep the dot in the result.
    :return: File’s extension. If there is none, an empty string is returned.
    """
    ext = os.path.splitext(str(filename))[1]
    if not keep_dot and ext:
        return ext[1:]
    return ext
