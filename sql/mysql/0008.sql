CREATE TABLE discriminator (
    `id` tinyint(1) NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `name` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_9`(`name`)) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE template_match (
    `obj_id` integer NOT NULL DEFAULT '',
    `template_id` integer NOT NULL DEFAULT '',
    `discriminator` tinyint(4) DEFAULT NULL,
    `type` tinyint(1) NOT NULL DEFAULT '0',
     CONSTRAINT `obj_templates_obj` FOREIGN KEY (`obj_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `obj_templates_template` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `templatematch_discr` FOREIGN KEY (`discriminator`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE templates (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(50) COLLATE utf8_general_ci DEFAULT NULL,
    `data` text COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `site_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE obj
    MODIFY COLUMN `discriminator` tinyint(4) NULL DEFAULT NULL;
ALTER TABLE site_users
    DROP KEY `x_1`,
    ADD UNIQUE KEY `x_5`(`site_id`,`user_id`);
ALTER TABLE sites
    DROP KEY `x_3`,
    DROP KEY `x_2`,
    ADD UNIQUE KEY `x_6`(`name`),
    ADD UNIQUE KEY `x_7`(`domain`);
ALTER TABLE urls
    DROP KEY `x_4`,
    ADD UNIQUE KEY `x_8`(`uid`);
ALTER TABLE obj
    ADD CONSTRAINT `obj_discr` FOREIGN KEY (`discriminator`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict;
