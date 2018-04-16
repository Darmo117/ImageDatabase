# Image Library
Image Library let's you manage images by associating tags to them.

- Search tagged images
- Add images and associate tags to them
- Remove/replace added images
- Modify/remove tags of added images
- Associate types to tags

## Installation
Image Library is *not* available on PyPI. Might be some day… I dunno…

You need to build the application in order to use it. To do so, run `build.py` and wait for it to complete.
Once it is done, go into `build/` and copy the application directory (`Image-Library/`) where you want to.

## Usage
To launch the application, simply run `ImageLibrary.py`.

Run `ImageLibrary_cmd.py` to start an SQLite command line to interact directly with the database.

**Important: Do not use non-ASCII letters in tag names as the query analyser currently doesn't recognize them.**
I'll try to fix that in a future version.

## Updating
Delete all files except `library.sqlite3`, which is the database file. Follow installation instructions (cf. Usage).

Check in `db_converter/` directory if a file named `v#_to_v§.py`, where `§` is the
current version and `#` the previous one.
If there is such file it means the database structure has changed between the two versions.
You need to run the following command to update your database:
```
python ./db_converters/v#_to_v§.py library.sqlite3
```
A backup of the old version will be created under the name `library-old_#.sqlite3`.

## Documentation
To come…

## Requirements
- Python 3.6+ (That's the version I'm using, might work with older versions, never tested it)
- [PyQt5](http://pyqt.sourceforge.net/Docs/PyQt5/) (GUI)
- sqlite3 (Database; generally installed with Python)
- [Lark](https://github.com/erezsh/lark) (Queries analysis)
- [SymPy](http://www.sympy.org/fr/index.html) (Queries simplification)

## Author
- Damien Vergnet [@Darmo117](https://github.com/Darmo117)
