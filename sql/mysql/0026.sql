CREATE TABLE demo (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(250) COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `comment_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
