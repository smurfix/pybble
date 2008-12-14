CREATE TABLE comment (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(250) COLLATE utf8_general_ci DEFAULT NULL,
    `data` text COLLATE utf8_general_ci DEFAULT NULL,
    `added` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `comment_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE wikipage
    DROP FOREIGN KEY `wikipage.id`;
