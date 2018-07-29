# Image Library
Image Library let's you manage images by associating tags to them.

- Search tagged images
- Add images and associate tags to them
- Remove/replace added images
- Modify/remove tags of added images
- Associate types to tags

*GIFs are not animated because I don't know how to do that. Any help would be really appreciated!*

## Installation
Image Library is *not* available on PyPI. Might be some day… I dunno… When I take the time to look into it…

You need to build the application in order to use it. To do so, run `build.py` and wait for it to complete.
Once it is done, go into `build/` and copy the application directory (`Image-Library/`) where you want to.

## Usage
### Main application
To launch the application, simply run `ImageLibrary.py`.

You can search for images by typing queries in the search field.
Syntax is as follow:
- `a` will match images with tag `a`
- `a b` will match images with both tags `a` and `b`
- `a + b` will match images with tags `a` or `b` or both
- `-a` will match images *without* tag `a`
- `type:png` will match images that are PNG files
- `name:*awesome\ pic*` will match images that contain the string `awesome pic` (note the `\ ` to escape the space character)

More complex queries can be written using parentheses.

Example:
```
a (b + c) + -(d e) type:jpg
```
Let's explain it:
- `a (b + c)` returns the set of images with both tags `a` and `b` or both tags `a` and `c`
- `-(d + e) type:jpg` = `-d -e type:jpg` returns the set of JPEG images without tags `d` and `e`

The result is the union of both image sets.

### Command Line
Run `ImageLibrary_cmd.py` to start an SQLite command line to interact directly with the database.

---

If you encounter an unexpected error, check the error log located in `logs/error.log` and see if there's an error.
You can send me a message with the error and a description of how you got this error, that would be really appreciated!

Don't mind the "Export As Playlist…" menu. It generates a playlist of the currently listed images.
These playlists are used by an application I haven't released yet.

## Updating
Delete all files except `library.sqlite3`, which is the database file.
Once done, follow installation instructions (cf. Usage section).

Check in `db_converter/` directory if there's a file named `v#_to_v§.py`, where `§` is the
current version and `#` the previous one.
If there is such file it means the database structure has changed between the two versions.
You need to run the following command to update your database:
```
python ./db_converters/v#_to_v§.py library.sqlite3
```
A backup of the old version will be created under the name `library-old_#.sqlite3`.

One day I'll try to find a way to automate this step.

## Documentation
To come…

## Requirements
- Python 3.6+ (That's the version I'm using, might work with older 3.x versions, never tested it)
- [PyQt5](http://pyqt.sourceforge.net/Docs/PyQt5/) (GUI)
- sqlite3 (Database; generally installed with Python)
- [Lark](https://github.com/erezsh/lark) (Queries analysis)
- [SymPy](http://www.sympy.org/fr/index.html) (Queries simplification)

## Author
- Damien Vergnet [@Darmo117](https://github.com/Darmo117)
