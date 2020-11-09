drop table if exists url;
create table url (
  id integer primary key autoincrement,
  long text not null,
  short text not null
);
