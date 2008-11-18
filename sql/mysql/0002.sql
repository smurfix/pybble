CREATE TABLE obj (
    `discriminator` integer DEFAULT NULL,
    `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
     PRIMARY KEY(`id`)) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE urls
    ADD COLUMN `id` integer NOT NULL DEFAULT '',
    MODIFY COLUMN `uid` varchar(140) COLLATE utf8_general_ci NULL DEFAULT NULL,
    MODIFY COLUMN `target` varchar(500) COLLATE utf8_general_ci NULL DEFAULT NULL AFTER id,
    DROP PRIMARY KEY,
    ADD PRIMARY KEY(`id`);
#uid: !null, default ''
#target: after public

ALTER TABLE urls
    ADD CONSTRAINT `None` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
