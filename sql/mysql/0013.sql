CREATE TABLE groupmembers (
    `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `user_id` integer DEFAULT NULL,
    `group_id` integer DEFAULT NULL,
    `excluded` bool NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     CONSTRAINT `member_group` FOREIGN KEY (`group_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `member_user` FOREIGN KEY (`user_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE groups (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(30) COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE permissions
    ADD COLUMN `inherit` bool NULL DEFAULT NULL,
    ADD COLUMN `discriminator` tinyint(4) NULL DEFAULT NULL;
ALTER TABLE users
    DROP COLUMN `verified`;
ALTER TABLE permissions
    ADD CONSTRAINT `obj_discr` FOREIGN KEY (`discriminator`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict;
