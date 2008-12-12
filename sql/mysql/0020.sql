CREATE TABLE bindata (
    `id` integer NOT NULL DEFAULT '',
    `mime_id` integer DEFAULT NULL,
    `name` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `hash` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_15`(`hash`),
     CONSTRAINT `mimetype_id` FOREIGN KEY (`mime_id`) REFERENCES `mimetype` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `bindata_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE breadcrumbs
    DROP FOREIGN KEY `templatematch_discr`;
CREATE TABLE mimeext (
    `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `mime_id` integer DEFAULT NULL,
    `ext` varchar(10) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_9`(`ext`),
     CONSTRAINT `mimetype_id` FOREIGN KEY (`mime_id`) REFERENCES `mimetype` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE mimetype (
    `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `name` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `typ` varchar(15) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `subtyp` varchar(15) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `ext` varchar(15) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_19`(`name`)) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE staticfile (
    `id` integer NOT NULL DEFAULT '',
    `path` varchar(200) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     CONSTRAINT `staticfile_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE storage (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(250) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `path` varchar(250) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `url` varchar(250) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_12`(`name`),
     UNIQUE KEY `x_11`(`url`),
     UNIQUE KEY `x_10`(`path`),
     CONSTRAINT `storage_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE wanttracking
    DROP FOREIGN KEY `templatematch_discr`;
ALTER TABLE wanttracking
    ADD COLUMN `track_new` bool NOT NULL DEFAULT '',
    ADD COLUMN `track_mod` bool NOT NULL DEFAULT '',
    ADD COLUMN `track_del` bool NOT NULL DEFAULT '',
    MODIFY COLUMN `discr` tinyint(4) NULL DEFAULT NULL,
    DROP COLUMN `inherit`,
    DROP COLUMN `mods`;
