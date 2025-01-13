use office_translator;
-- ALTER TABLE tasks ADD UNIQUE KEY md5_source_language_target_language(md5, source_language, target_language);
ALTER TABLE tasks ADD auto_resize_text BOOLEAN not null default 1;
