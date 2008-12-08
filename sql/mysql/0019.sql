ALTER TABLE breadcrumbs
    DROP FOREIGN KEY `template_id`;
ALTER TABLE changes
    DROP FOREIGN KEY `template_id`;
CREATE TABLE deleted (
    `id` integer NOT NULL DEFAULT '',
    `comment` varchar(200) COLLATE utf8_general_ci DEFAULT NULL,
    `old_superparent_id` integer DEFAULT NULL,
    `old_owner_id` integer DEFAULT NULL,
    `timestamp` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `delete_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `obj_super` FOREIGN KEY (`old_superparent_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `obj_owner` FOREIGN KEY (`old_owner_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE template_match
    DROP FOREIGN KEY `group_id`;
CREATE TABLE tracking (
    `id` integer NOT NULL DEFAULT '',
    `timestamp` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `tracker_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE usertracking (
    `id` integer NOT NULL DEFAULT '',
    `comment` varchar(200) COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `usertracker_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE wanttracking (
    `id` integer NOT NULL DEFAULT '',
    `discr` tinyint(4) NOT NULL DEFAULT '0',
    `inherit` bool DEFAULT NULL,
    `email` bool NOT NULL DEFAULT '',
    `mods` bool NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     CONSTRAINT `templatematch_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE wikipage
    DROP FOREIGN KEY `template_id`;
ALTER TABLE sites
    ADD COLUMN `tracked` datetime NOT NULL DEFAULT '0000-00-00 00:00:00';
