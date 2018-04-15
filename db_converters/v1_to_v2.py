#!C:\ProgramData\Anaconda3\python.exe

import os
import sqlite3
import sys

if len(sys.argv) != 2:
    print("Expected database file!", file=sys.stderr)
    sys.exit(-1)

file = sys.argv[1]
name, ext = os.path.splitext(file)
old_file = name + "-old" + ext
os.rename(file, old_file)
if os.path.exists(file):
    os.remove(file)

v1_connection = sqlite3.connect(old_file)

v2_connection = sqlite3.connect(file)
v2_connection.executescript("""
pragma foreign_keys = on;

create table if not exists images (
  id integer primary key autoincrement,
  path text unique not null
);

create table if not exists tag_types (
  id integer primary key autoincrement,
  label text unique not null,
  symbol text unique not null
);

create table if not exists tags (
  id integer primary key autoincrement,
  label text unique not null,
  type_id integer,
  foreign key (type_id) references tag_types(id) on delete set null
);

create table if not exists image_tag (
  image_id integer not null,
  tag_id integer not null,
  primary key (image_id, tag_id),
  foreign key (image_id) references images(id) on delete cascade,
  foreign key (tag_id) references tags(id) on delete cascade
);
""")

cursor = v1_connection.execute("SELECT id, path FROM images")
for entry in cursor.fetchall():
    v2_connection.execute("INSERT INTO images (id, path) VALUES(?, ?)", entry)
v2_connection.commit()
cursor.close()

cursor = v1_connection.execute("SELECT id, label FROM tags")
for entry in cursor.fetchall():
    v2_connection.execute("INSERT INTO tags (id, label) VALUES(?, ?)", entry)
v2_connection.commit()
cursor.close()

cursor = v1_connection.execute("SELECT image_id, tag_id FROM image_tag")
for entry in cursor.fetchall():
    v2_connection.execute("INSERT INTO image_tag (image_id, tag_id) VALUES(?, ?)", entry)
v2_connection.commit()
cursor.close()

v1_connection.close()
v2_connection.close()
