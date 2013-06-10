if not exists customers;

create table customers (
  id integer primary key autoincrement,
  name text not null,
  address text not null,
  lat double not null,
  lng double not null,
  additionaldata text, not null
);
