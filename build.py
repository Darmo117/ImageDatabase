#!/usr/bin/python3
import pathlib
import shutil

TO_COPY = [
    'ImageLibrary.py',
    'ImageLibrary_cmd.py',
    'setup.sh',
    'setup.bat',
    'requirements.txt',
    'app/',
    'LICENSE',
    'README.md'
]
BUILD_DIR = pathlib.Path('build/Image-Library').absolute()

if BUILD_DIR.exists():
    print('Cleaning build directory…')
    shutil.rmtree(BUILD_DIR)

print('Creating build directory…')
BUILD_DIR.mkdir(parents=True)

print('Copying files…')
for file in TO_COPY:
    to_copy = pathlib.Path(file).absolute()
    dest = BUILD_DIR / file
    if to_copy.is_dir():
        shutil.copytree(to_copy, dest)
    else:
        shutil.copy(to_copy, dest)

print('Creating configuration file…')
with open(BUILD_DIR / 'config.ini', mode='w', encoding='UTF-8') as to_copy:
    contents = """
# You can edit this file to change some options.
# Changing any option while the application is running will have no immediate
# effect, you’ll have to restart it in order to apply the changes.

[UI]
# App’s language
Language = en

[Images]
# Load thumbnails: yes or no
LoadThumbnails = yes
# Size of thumbnails in list
ThumbnailSize = 200
# Minimum number of images in query result to disable thumbnails (to avoid running out of memory)
ThumbnailLoadThreshold = 50

[Database]
# Path to the database file. Cannot be changed from within the application.
File = library.sqlite3
    """.strip()
    to_copy.write(contents)

print('Done.')
