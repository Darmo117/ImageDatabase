# Image Library

Image Library lets you manage images by associating tags to them.

- Add and tag images
- Search tagged images
- Remove images
- Replace images while keeping all associated tags
- Edit tags of images
- Manage tags (create, remove, associate type)
- Export query results as “playlists” (XML files)

*GIFs are not animated because I don’t know how to do that yet. Any help would be really appreciated!*

## Installation

Image Library is *not* available on PyPI. Might be some day… I dunno… When I take the time to look into that.

### Version 3.2+

Download the attached zip file in the release then unpack it where you want to install the app. Once unpacked, run the
`setup.sh` file to install all required dependencies.

### Version 3.1 and prior

You need to build the application in order to use it. To do so, run `build.py` and wait for it to complete. Once it is
done, go into `build/` and copy the application directory (`Image-Library/`) where you want to.

## Updating

Delete all files and directories except database (`library.sqlite3`, may differ if changed in config file) and
config (`config.ini`) files. Once done, follow [installation instructions](#Installation). Discard the new `config.ini`
file if you want to keep the previous configuration.

For versions 3.2+, database files are automatically updated. A backup of the old version will be created under the
name `<file name>-old_<old version>.sqlite3`. For instance, updating the file `library.sqlite3` from version 3.1 will
create the backup file `library-old_3.1.sqlite3`.

## Usage

### Main application

To launch the application, simply run `./ImageLibrary.py`. If it does not work, you might need to perform the following
command: `chmod u+x ./ImageLibrary.py`.

You can search for images by typing queries in the search field. Syntax is as follow:

- `a` will match images with tag `a`
- `a b` will match images with both tags `a` *and* `b`
- `a + b` will match images with tags `a` *or* `b` or *both*
- `-a` will match images *without* tag `a`
- `type:png` will match images that are *PNG* files
- `name:*awesome\ pic*` will match images whose *name* contains the string `awesome pic` (note the `\ ` to escape the
  space character); the `*` character matches any character, 0 or more times

More complex queries can be written using parentheses.

Example:

```
a (b + c) + -(d e) type:jpg
```

Here’s how to interpret it:

- `a (b + c)` returns the set of images with both tags `a` and `b` and/or both tags `a` and `c`
- `-(d + e) type:jpg` = `-d -e type:jpg` returns the set of JPEG images without tags `d` nor `e`

The result is the union of both image sets.

The application also supports compound tags, i.e. tags defined from tag queries (e.g.: tag `animal` could be defined as
`cat + dog + bird`). You cannot tag images directly with compound tags, they exist only for querying purposes.

### Command Line Tool

Run `./ImageLibrary_cmd.py` to start an SQLite command line to interact directly with the database.

## Config File

The following configurations can be modified in the `config.ini` file.

- `File`: database file path and name relative to the app’s directory
- `LoadThumbnails`: `true` or `false` to load or not thumbnails (can be changed from app)
- `ThumbnailSize`: thumbnail size in pixels (can be changed from app)

---

If you encounter an unexpected error, check the error log located in `logs/error.log` and see if there’s an error. You
can send me a message with the error and a description of how you got this error, that would be really appreciated!

## Documentation

To come…

## Requirements

- [Python 3.8](https://www.python.org/downloads/release/python-380/) or above (Will *not* work with older versions)
- [PyQt5](https://pypi.org/project/PyQt5/) (GUI)
- [Lark](https://pypi.org/project/lark-parser/) (Query parsing)
- [SymPy](https://pypi.org/project/sympy/) (Query simplification)
- [scikit-image](https://pypi.org/project/scikit-image/) (Image comparison) \[experimental feature]
- [OpenCV2](https://pypi.org/project/cv2imageload/) (Image comparison)

See [requirements.txt](https://github.com/Darmo117/ImageDatabase/blob/master/requirements.txt) for full list.

## Author

- Damien Vergnet [@Darmo117](https://github.com/Darmo117)
