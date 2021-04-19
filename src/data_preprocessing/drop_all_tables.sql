-- drop all tables and indexes and recover deleted space
PRAGMA writable_schema = 1;
delete from sqlite_master where type in ('table', 'index');
PRAGMA writable_schema = 0;
VACUUM;