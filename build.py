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
    dest = os.path.join(BUILD_DIR, file)
    if os.path.isdir(file):
        shutil.copytree(file, dest)
    else:
        shutil.copy(file, dest)

print('Creating configuration file…')
with open(os.path.join(BUILD_DIR, 'config.ini'), mode='w', encoding='UTF-8') as f:
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
    f.write(contents)

print('Done.')
