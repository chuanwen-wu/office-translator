create database if not exists office_translator;

use office_translator;

create table if not exists tasks (
    id int auto_increment primary key,
    md5 char(32) not null,
    status int not null default 0 comment '0: pending, 1: processing, 2: completed, 3: failed',
    file_name varchar(255) not null,
    source_language varchar(255),
    target_language varchar(255),
    dont_translate_list varchar(1024),
    input_file_path varchar(255),
    output_file_path varchar(255),
    callback_url varchar(4096),
    user_id varchar(255),
    error_msg varchar(1024),
    created_at datetime not null default current_timestamp,
    updated_at datetime not null default current_timestamp on update current_timestamp
);
-- ALTER TABLE tasks ADD UNIQUE KEY md5_source_language_target_language(md5, source_language, target_language);
-- ALTER TABLE tasks ADD error_msg varchar(1024);
