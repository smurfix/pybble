CREATE TABLE breadcrumbs (
    `id` integer NOT NULL DEFAULT '',
    `discr` tinyint(4) NOT NULL DEFAULT '0',
    `seq` integer DEFAULT NULL,
    `visited` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `templatematch_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `template_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
