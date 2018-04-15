#!C:\ProgramData\Anaconda3\python.exe

import os
import shutil

TO_COPY = ["ImageLibrary.py", "ImageLibrary_cmd.py", "config.py", "app/", "icons/", "db_converters/"]
BUILD_DIR = "build/Image-Library/"

if os.path.exists(BUILD_DIR):
    print("Cleaning build directory...")
    shutil.rmtree(BUILD_DIR)

print("Creating build directory...")
os.makedirs(BUILD_DIR)

print("Copying files...")
for file in TO_COPY:
    dest = BUILD_DIR + file
    if file[-1] == "/":
        shutil.copytree(file, dest)
    else:
        shutil.copy(file, dest)

print("Editing config...")
with open("config.py") as f:
    lines = f.readlines()
with open(BUILD_DIR + "config.py", "w") as f:
    for line in lines:
        if line.startswith("DATABASE"):
            line = 'DATABASE = "library.sqlite3"\n'
        f.write(line)

print("Done.")
