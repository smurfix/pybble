CREATE TABLE wikipage (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(50) COLLATE utf8_general_ci DEFAULT NULL,
    `data` text COLLATE utf8_general_ci DEFAULT NULL,
    `modified` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `template_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
