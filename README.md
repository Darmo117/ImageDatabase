# Image Library

Image Library lets you manage images by associating tags to them.

Main features:

- Tag images
- Search tagged images
- Replace/move image files while keeping all associated tags
- Manage tags (create, remove, associate type)
- Tag completion in queries and image tags editor
- Export query results as “playlists” (XML files)
- Apply pattern-based transformations to images paths
- List similar images (hash-based)
- Fully translated interface, available in English, French, and Esperanto
- Integrated SQL console
- Database auto-update

## Installation

Image Library is *not* available on PyPI. Might be some day… I dunno… When I take the time to look into that.

### Version 4.0+

Download the attached zip file in the release then unpack it where you want to install the app. Once unpacked, run the
`setup.sh` file to install all required dependencies.

### Version 3.1 and prior

You need to build the application in order to use it. To do so, run `build.py` and wait for it to complete. Once it is
done, go into `build/` and copy the application directory (`Image-Library/`) where you want to.

## Updating

Delete all files and directories except database (`library.sqlite3`, may differ if changed in config file) and
config (`config.ini`) files. Once done, follow [installation instructions](#Installation). Discard the new `config.ini`
file if you want to keep the previous configuration.

For versions 4.0+, database files are automatically updated. A backup of the old version will be created under the
name `<file name>-old_<old version>.sqlite3`. For instance, updating the file `library.sqlite3` from version 3.1 will
create the backup file `library-old_3.1.sqlite3`.

## Usage

### Main application

#### <span id="run-linux">Launch on Linux</span>

Simply run `./ImageLibrary.py`. If it does not work, you might need to change file’s user
rights: `chmod u+x ./ImageLibrary.py`.

#### Launch on Windows

Just run `python3 ImageLibrary.py`.

#### Registering images

Go through the _File_ menu and click on _Add Files_ to add images or _Add Directory_ to import all images from a
directory; or you can simply drag-and-drop files or directories into the main window.

You should see a dialog window with a preview of an image and a text field. This text field is where you have to type
the tags for the displayed image. Once you’re satisfied, click on _Apply & Continue_ or _Finish_ to go to the next
image. You can click on _Skip_ to skip the current image and go directly to the next one.

While editing tags, you can choose where to move the current image by clicking on _Move to…_; the path is then displayed
next to the button.

If the application found similar images already registered, a button labelled _Similar Images…_ will appear above the
text area. It will show a list of similar images, ordered by decreasing estimated similarity. You can select one of
these images and copy its tags by clicking on _Copy Tags_ (**Warning**: it will replace all tags in the text box).

#### Searching for registered images

You can search for images by typing queries in the search field. Syntax is as follow:

- `a` will match images with tag `a`
- `a b` will match images with both tags `a` *and* `b`
- `a + b` will match images with tags `a` *or* `b` or *both*
- `-a` will match images *without* tag `a`
- `ext:"png"` will match images that are *PNG* files
- `name:"*awesome pic*"` will match images whose *name* contains the string `awesome pic`; the `*` character matches any
  character, 0 or more times
- `path:"/home/user/images/summer?.png"` will match images with *paths* like `/home/user/images/summer.png`,
  `/home/user/images/summer1.png`, `/home/user/images/summers.png`, etc.; the `?` character matcher any character 0 or 1
  times
- `similar_to:"/home/user/images/house.png"` will match all images that are similar to `/home/user/images/house.png`
  (if it is registered in the database)

Special tags accept two types of values: plain text, in between `"` and regular expressions (regex) in between `/`.

As seen in the examples above, plain text values accept two special characters, `*` and `?` that match respectively 0 or
more, and 0 or 1 characters. You can disable them by putting a `\ ` before (e.g.: `\*` will match the character `*`
literally). You also have to escape all single `\ ` by doubling them: `\\`. For instance, to match all images whose path
begin with `C:\Users\me\images\ `, you will have to type `path:"C:\\Users\\me\\images\\*"`. If a path or file name
contains a double quote, you have to escape it in the same way: `\"`.

Regular expressions follow Python’s format. See [this page](https://www.w3schools.com/python/python_regex.asp) for
explanations of the syntax. Note that you have to escape all `/` too, as this is the delimiter.

More complex queries can be written by grouping with parentheses.

Example:

```
a (b + c) + -(d e) ext:"jp?g"
```

Here’s how to interpret it:

- `a (b + c)` returns the set of images with both tags `a` and `b` and/or both tags `a` and `c`
- `-(d + e) ext:"jp?g"` = `-d -e ext:"jp?g"` returns the set of JPG images without tags `d` nor `e`; note the `?` to
  match both `jpg` and `jpeg` extensions

The result is the union of both image sets.

The application also supports compound tags, i.e. tags defined from tag queries (e.g.: tag `animal` could be defined as
`cat + dog + bird`). You cannot tag images directly with compound tags, they exist only for querying purposes.

### External command line tool

An external SQLite command line interface is available to interact directly with the database. Use with extreme caution
as you may break the database’s structure and render it unusable by the app.

Linux: Run `./ImageLibrary_cmd.py`. If you get errors, refer to [Launch on Linux](#run-linux) section.

Windows: Run `python3 ImageLibrary_cmd.py`.

## Configuration file

The following configurations can be modified in the `config.ini` file. If the file does not exist, launch the
application at least once to generate it.

- Section `[Database]`:
    - `File`: path to database file; can be absolute or relative to the app’s root directory
- Section `[Images]`:
    - `LoadThumbnails`: `true` or `false` to load or not thumbnails (can be changed from app)
    - `ThumbnailSize`: thumbnail size in pixels (can be changed from app)
    - `ThumbnailLoadThreshold`: maximum number of thumbnails that can be displayed without warning when querying images
- Section `[UI]`:
    - `Language`: language code of app’s interface; can be either `en` for English, `fr` for French, or `eo` for
      Esperanto

## Found a bug?

If you encounter a bug or the app crashed, check the error log located in `logs/error.log` and see if there’s an error.
You can send me a message or open an issue with the error and a description of how you got this error, that would be
really appreciated!

## Documentation

Soon…

## Requirements

- [Python 3.8](https://www.python.org/downloads/release/python-380/) or above (Will *not* work with older versions)
- [PyQt5](https://pypi.org/project/PyQt5/) (GUI)
- [Lark](https://pypi.org/project/lark-parser/) (Query parsing)
- [SymPy](https://pypi.org/project/sympy/) (Query simplification)
- [scikit-image](https://pypi.org/project/scikit-image/) (Image comparison)
- [OpenCV2](https://pypi.org/project/cv2imageload/) (Image comparison)
- [Pyperclip](https://pypi.org/project/pyperclip/) (Copy text to clipboard)

See [requirements.txt](https://github.com/Darmo117/ImageDatabase/blob/master/requirements.txt) for up-to-date list.

## Author

- Damien Vergnet [@Darmo117](https://github.com/Darmo117)
