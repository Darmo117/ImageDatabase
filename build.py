#!/usr/bin/python3
import os
import shutil

TO_COPY = ['ImageLibrary.py', 'ImageLibrary_cmd.py', 'setup.sh', 'requirements.txt', 'app/', 'LICENSE', 'README.md']
BUILD_DIR = 'build/Image-Library/'

if os.path.exists(BUILD_DIR):
    print('Cleaning build directory…')
    shutil.rmtree(BUILD_DIR)

print('Creating build directory…')
os.makedirs(BUILD_DIR)

print('Copying files…')
for file in TO_COPY:
    dest = BUILD_DIR + file
    if file[-1] == '/':
        shutil.copytree(file, dest)
    else:
        shutil.copy(file, dest)

print('Creating config…')
with open(BUILD_DIR + 'config.ini', 'w') as f:
    contents = """
# You can edit this file to change some options.
# Changing any option while the application is running will have no immediate
# effect, you’ll have to restart it in order to apply the changes.

[Database]
# Path to the database file.
File = library.sqlite3

# These options should be modified from the application.
[Images]
# Load thumbnails: yes or no
LoadThumbnails = yes
# Size of thumbnails in list
ThumbnailSize = 200
# Minimum number of images in query result to disable thumbnails (to avoid running out of memory)
ThumbnailLoadThreshold = 50
    """.strip()
    f.write(contents)

print('Done.')
