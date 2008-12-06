CREATE TABLE changes (
    `id` integer NOT NULL DEFAULT '',
    `timestamp` timestamp DEFAULT NULL,
    `data` text COLLATE utf8_general_ci DEFAULT NULL,
    `comment` varchar(200) COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `template_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
