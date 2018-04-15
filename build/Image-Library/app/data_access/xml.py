import xml.etree.ElementTree as ETree


def write_playlist(file, images):
    playlist = ETree.Element("playlist")
    for image in images:
        item = ETree.SubElement(playlist, "image")
        item.text = image.path
        item.set("rotation", "0")
    tree = ETree.ElementTree(playlist)
    tree.write(file, encoding="UTF-8", xml_declaration=True)
