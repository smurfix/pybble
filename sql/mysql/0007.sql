CREATE TABLE permissions (
    `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `user_id` integer NOT NULL DEFAULT '',
    `obj_id` integer NOT NULL DEFAULT '',
    `right` integer DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `permission_obj` FOREIGN KEY (`obj_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `permission_user` FOREIGN KEY (`user_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE users
    DROP FOREIGN KEY `permission_obj`,
    DROP FOREIGN KEY `permission_user`;
ALTER TABLE site_users
    DROP KEY `x_1`,
    ADD UNIQUE KEY `x_5`(`site_id`,`user_id`);
ALTER TABLE sites
    DROP KEY `x_4`,
    DROP KEY `x_3`,
    ADD UNIQUE KEY `x_7`(`name`),
    ADD UNIQUE KEY `x_6`(`domain`);
ALTER TABLE urls
    DROP KEY `x_2`,
    ADD UNIQUE KEY `x_8`(`uid`);
ALTER TABLE users
    MODIFY COLUMN `id` integer NOT NULL DEFAULT '',
    DROP COLUMN `user_id`,
    DROP COLUMN `obj_id`,
    DROP COLUMN `right`;
