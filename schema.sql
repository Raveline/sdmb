drop table if exists dreams;
create table entries (
      dr_id integer primary key autoincrement,
      dr_title varchar(100) not null,
      dr_text text not null,
      dr_date date not null
);
