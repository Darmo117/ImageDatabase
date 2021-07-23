import typing as typ
import xml.etree.ElementTree as ETree

from .. import model


def write_playlist(file: str, images: typ.List[model.Image]):
    """
    Writes the given images as a playlist in the specified file.

    :param file: The output file.
    :param images: The image of the playlist.
    """
    playlist = ETree.Element('playlist')
    for image in images:
        item = ETree.SubElement(playlist, 'image')
        item.text = image.path
        item.set('rotation', '0')
    tree = ETree.ElementTree(playlist)
    tree.write(file, encoding='UTF-8', xml_declaration=True)
