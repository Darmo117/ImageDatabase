pragma foreign_keys = on;

create table images (
  id integer primary key autoincrement,
  path text unique not null
);

create table tag_types (
  id integer primary key autoincrement,
  label text not null unique,
  symbol text not null unique,
  color integer default 0
);

create table tags (
  id integer primary key autoincrement,
  label text unique not null,
  type_id integer
      references tag_types(id) on delete set null
);

create table image_tag (
  image_id integer not null
      references images(id) on delete cascade,
  tag_id integer not null
      references tags(id) on delete cascade,
  primary key (image_id, tag_id)
);
