pragma foreign_keys = on;

create table if not exists images (
  id integer primary key autoincrement,
  path text unique not null
);

create table if not exists tag_types (
  id integer primary key autoincrement,
  label text unique not null,
  symbol text unique not null,
  color integer default 0
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
