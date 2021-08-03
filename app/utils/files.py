"""Utility functions to handle files."""
import os
import pathlib
import typing as typ

from app import constants


def get_files_from_directory(directory: pathlib.Path, recursive: bool = True) -> typ.List[pathlib.Path]:
    """Returns all image files contained in the given directory.

    :param directory: The directory to look into.
    :param recursive: Whether to return images from all sub-directories.
    :return: The list of valid image files.
    :raise RecursionError: If the function reaches a depth of more than 20 sub-directories.
    """
    max_depth = 20

    def aux(root: pathlib.Path, depth: int = 0) -> typ.List[pathlib.Path]:
        if depth > max_depth:
            raise RecursionError(max_depth)
        files = []
        for f in root.glob('*'):
            if f.is_dir() and recursive:
                files.extend(aux(f, depth + 1))
            elif f.is_file() and accept_image_file(f):
                files.append(f.absolute())
        return files

    return aux(directory)


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
