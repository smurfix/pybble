#FK None fields: ['parent_id'] ['owner_id']
#FK None fields: ['parent_id'] ['superparent_id']
ALTER TABLE obj
    DROP FOREIGN KEY `None`,
    DROP FOREIGN KEY `None`;
CREATE TABLE site_users (
    `site_id` integer DEFAULT NULL,
    `user_id` integer DEFAULT NULL,
     FOREIGN KEY (`user_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     FOREIGN KEY (`site_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE sites (
    `id` integer NOT NULL DEFAULT '',
    `domain` varchar(100) COLLATE utf8_general_ci DEFAULT NULL,
    `name` varchar(50) COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE users (
    `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `username` varchar(30) COLLATE utf8_general_ci DEFAULT NULL,
    `first_name` varchar(30) COLLATE utf8_general_ci DEFAULT NULL,
    `last_name` varchar(30) COLLATE utf8_general_ci DEFAULT NULL,
    `email` varchar(100) COLLATE utf8_general_ci DEFAULT NULL,
    `password` varchar(30) COLLATE utf8_general_ci DEFAULT NULL,
    `verified` bool DEFAULT NULL,
    `first_login` datetime DEFAULT NULL,
    `last_login` datetime DEFAULT NULL,
    `user_id` integer DEFAULT NULL,
    `obj_id` integer DEFAULT NULL,
    `right` integer DEFAULT NULL,
     PRIMARY KEY(`id`),
     FOREIGN KEY (`obj_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     FOREIGN KEY (`user_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
#FK None fields: ['owner_id'] ['parent_id']
#FK None fields: ['owner_id'] ['parent_id']
#FK None fields: ['superparent_id'] ['parent_id']
#FK None fields: ['superparent_id'] ['parent_id']
ALTER TABLE obj
    DROP CONSTRAINT `None`,
    ADD FOREIGN KEY (`owner_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    DROP CONSTRAINT `None`,
    ADD FOREIGN KEY (`superparent_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
