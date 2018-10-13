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
- `name:*awesome\ pic*` will match images that contain the string `awesome pic` (note the `\ ` to escape the space
character)

More complex queries can be written using parentheses.

Example:
```
a (b + c) + -(d e) type:jpg
```
Let's explain it:
- `a (b + c)` returns the set of images with both tags `a` and `b` or both tags `a` and `c`
- `-(d + e) type:jpg` = `-d -e type:jpg` returns the set of JPEG images without tags `d` and `e`

The result is the union of both image sets.

The application also supports compound tags, i.e. tags defined from tag queries (e.g.: tag `animal` could be defined as
`cat + dog + bird`).

### Command Line
Run `ImageLibrary_cmd.py` to start an SQLite command line to interact directly with the database.

---

If you encounter an unexpected error, check the error log located in `logs/error.log` and see if there's an error.
You can send me a message with the error and a description of how you got this error, that would be really appreciated!

## Updating
Delete all files except `library.sqlite3`, which is the database file.
Once done, follow installation instructions (cf. Usage section).

When updating from 2.0 to 3.0, run the following command to update your database:
```
python ./db_converters/v2.0_to_v3.0.py library.sqlite3
```
A backup of the old version will be created under the name `library-old_2.0.sqlite3`.

From version 3.2 and forward, database files are automatically updated if needed and a back up created.

## Documentation
To come…

## Requirements
- Python 3.7+ (Will *not* work with older versions)
- [PyQt5](http://pyqt.sourceforge.net/Docs/PyQt5/) (GUI)
- sqlite3 (Database; generally installed with Python)
- [Lark](https://github.com/erezsh/lark) (Queries analysis)
- [SymPy](http://www.sympy.org/fr/index.html) (Queries simplification)

## Author
- Damien Vergnet [@Darmo117](https://github.com/Darmo117)
