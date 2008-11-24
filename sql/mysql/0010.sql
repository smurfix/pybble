ALTER TABLE templates
    DROP FOREIGN KEY `site_id`;
CREATE TABLE verifierbase (
    `id` tinyint(1) NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `name` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `cls` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_12`(`name`),
     UNIQUE KEY `x_13`(`cls`)) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
CREATE TABLE verifiers (
    `id` integer NOT NULL DEFAULT '',
    `base_id` tinyint(4) DEFAULT NULL,
    `code` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
    `repeated` datetime DEFAULT NULL,
    `timeout` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_9`(`code`),
     CONSTRAINT `verifier_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `verifier_base` FOREIGN KEY (`base_id`) REFERENCES `verifierbase` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
