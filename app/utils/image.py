"""Functions related to image hashing."""
import typing as typ

import cv2


def get_hash(image_path: str, diff_size: int = 8) -> typ.Optional[int]:
    """Computes the difference hash of the image at the given path.

    :param image_path: Image’s path.
    :param diff_size: Size of the difference matrix.
    :return: The hash or None if the image could not be opened.
    """
    image = cv2.imread(image_path)
    if image is None:
        return None
    # Convert the image to grayscale and compute the hash
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Resize the input image, adding a single column (width) so we can compute the horizontal gradient
    resized = cv2.resize(image, (diff_size + 1, diff_size))
    # Compute the (relative) horizontal gradient between adjacent column pixels
    diff = resized[:, 1:] > resized[:, :-1]
    # Convert the difference image to a hash
    # noinspection PyUnresolvedReferences
    return sum([2 ** i for i, v in enumerate(diff.flatten()) if v])


def compare_hashes(hash1: int, hash2: int, diff_size: int = 8) -> typ.Tuple[int, typ.Optional[float], bool]:
    """Compares two image hashes. Two hashes are considered similar if their Hamming distance
    is ≤ 10 (cf. http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html).

    Similarity confidence coefficient is computed using the following formula: (11 − d) / 11

    :param hash1: A hash.
    :param hash2: Another hash.
    :param diff_size: Size of the difference matrix.
    :return: Three values: the Hamming distance, the similarity confidence coefficient (None if third value is False)
        and a boolean indicating whether the images behind the hashes are similar or not.
    """
    threslhold = 10
    h1 = bin(hash1)[2:].rjust(diff_size ** 2, '0')
    h2 = bin(hash2)[2:].rjust(diff_size ** 2, '0')
    dist_counter = 0
    for n in range(len(h1)):
        if h1[n] != h2[n]:
            dist_counter += 1
    similar = dist_counter <= threslhold
    confidence = ((threslhold + 1) - dist_counter) / (threslhold + 1) if similar else None
    return dist_counter, confidence, similar


def image_size(image_path: str) -> typ.Optional[typ.Tuple[int, int]]:
    """Returns the size of the given image file.

    :param image_path: Path to the image.
    :return: A tuple (width, height) or None if file could not be opened.
    """
    image = cv2.imread(image_path)
    if image is None:
        return None
    return image.shape[1], image.shape[0]
