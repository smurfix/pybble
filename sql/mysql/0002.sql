Do("""CREATE TABLE bindata (
    `id` integer NOT NULL DEFAULT '',
    `mime_id` integer DEFAULT NULL,
    `name` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `hash` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `timestamp` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_8`(`hash`),
     CONSTRAINT `mimetype_id` FOREIGN KEY (`mime_id`) REFERENCES `mimetype` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `bindata_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE breadcrumbs (
    `id` integer NOT NULL DEFAULT '',
    `discr` tinyint(4) NOT NULL DEFAULT '0',
    `visited` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `breadcrumb_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `breadcrumb_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE changes (
    `id` integer NOT NULL DEFAULT '',
    `timestamp` timestamp DEFAULT NULL,
    `data` text COLLATE utf8_general_ci DEFAULT NULL,
    `comment` varchar(200) COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `change_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE comment (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(250) COLLATE utf8_general_ci DEFAULT NULL,
    `data` text COLLATE utf8_general_ci DEFAULT NULL,
    `added` timestamp DEFAULT NULL,
    `renderer_id` tinyint(4) DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `comment_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `cmt_renderer` FOREIGN KEY (`renderer_id`) REFERENCES `renderer` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE deleted (
    `id` integer NOT NULL DEFAULT '',
    `comment` varchar(200) COLLATE utf8_general_ci DEFAULT NULL,
    `old_superparent_id` integer DEFAULT NULL,
    `old_owner_id` integer DEFAULT NULL,
    `timestamp` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `delete_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `obj_super` FOREIGN KEY (`old_superparent_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `obj_owner` FOREIGN KEY (`old_owner_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE demo (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(250) COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `comment_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE discriminator (
    `id` tinyint(1) NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `name` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_1`(`name`)) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE groupmembers (
    `id` integer NOT NULL DEFAULT '',
    `excluded` bool NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE groups (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(30) COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE mimeext (
    `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `mime_id` integer DEFAULT NULL,
    `ext` varchar(10) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_2`(`ext`),
     CONSTRAINT `mimetype_id` FOREIGN KEY (`mime_id`) REFERENCES `mimetype` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE mimetype (
    `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `name` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `typ` varchar(15) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `subtyp` varchar(15) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `ext` varchar(15) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_12`(`name`)) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE obj (
    `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `discriminator` tinyint(4) DEFAULT NULL,
    `owner_id` integer DEFAULT NULL,
    `parent_id` integer DEFAULT NULL,
    `superparent_id` integer DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `obj_owner` FOREIGN KEY (`owner_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `obj_super` FOREIGN KEY (`superparent_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `obj_discr` FOREIGN KEY (`discriminator`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `obj_parent` FOREIGN KEY (`parent_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE permissions (
    `id` integer NOT NULL DEFAULT '',
    `right` integer NOT NULL DEFAULT '',
    `inherit` bool DEFAULT NULL,
    `discr` tinyint(4) NOT NULL DEFAULT '0',
    `new_discr` tinyint(4) DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `obj_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `obj_new_discr` FOREIGN KEY (`new_discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE renderer (
    `id` tinyint(1) NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `name` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `cls` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_15`(`name`),
     UNIQUE KEY `x_14`(`cls`)) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE site_users (
    `site_id` integer NOT NULL DEFAULT '',
    `user_id` integer NOT NULL DEFAULT '',
     UNIQUE KEY `x_13`(`site_id`,`user_id`),
     CONSTRAINT `site_users_user` FOREIGN KEY (`user_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `site_users_site` FOREIGN KEY (`site_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE sites (
    `id` integer NOT NULL DEFAULT '',
    `domain` varchar(100) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `name` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `tracked` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_7`(`name`),
     UNIQUE KEY `x_6`(`domain`),
     CONSTRAINT `site_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE staticfile (
    `id` integer NOT NULL DEFAULT '',
    `path` varchar(200) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `modified` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `staticfile_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE storage (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(250) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `path` varchar(250) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `url` varchar(250) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_5`(`name`),
     UNIQUE KEY `x_4`(`url`),
     UNIQUE KEY `x_3`(`path`),
     CONSTRAINT `storage_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE template_match (
    `id` integer NOT NULL DEFAULT '',
    `data` text COLLATE utf8_general_ci DEFAULT NULL,
    `modified` timestamp DEFAULT NULL,
    `discr` tinyint(4) NOT NULL DEFAULT '0',
    `detail` tinyint(1) NOT NULL DEFAULT '0',
    `inherit` bool DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `templatematch_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `template_match_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE templates (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `data` text COLLATE utf8_general_ci DEFAULT NULL,
    `modified` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `template_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE tracking (
    `id` integer NOT NULL DEFAULT '',
    `timestamp` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `tracker_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE users (
    `id` integer NOT NULL DEFAULT '',
    `username` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `first_name` varchar(30) COLLATE utf8_general_ci DEFAULT NULL,
    `last_name` varchar(30) COLLATE utf8_general_ci DEFAULT NULL,
    `email` varchar(100) COLLATE utf8_general_ci DEFAULT NULL,
    `password` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `first_login` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
    `last_login` datetime DEFAULT NULL,
    `feed_age` tinyint(4) NOT NULL DEFAULT '0',
    `feed_pass` varchar(30) COLLATE utf8_general_ci DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `user_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE usertracking (
    `id` integer NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     CONSTRAINT `usertracker_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE verifierbase (
    `id` tinyint(1) NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `name` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `cls` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_10`(`name`),
     UNIQUE KEY `x_11`(`cls`)) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE verifiers (
    `id` integer NOT NULL DEFAULT '',
    `base_id` tinyint(4) DEFAULT NULL,
    `code` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
    `repeated` datetime DEFAULT NULL,
    `timeout` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_9`(`code`),
     CONSTRAINT `verifier_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `verifier_base` FOREIGN KEY (`base_id`) REFERENCES `verifierbase` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE wanttracking (
    `id` integer NOT NULL DEFAULT '',
    `discr` tinyint(4) DEFAULT NULL,
    `email` bool NOT NULL DEFAULT '',
    `track_new` bool NOT NULL DEFAULT '',
    `track_mod` bool NOT NULL DEFAULT '',
    `track_del` bool NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     CONSTRAINT `wanttracking_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict,
     CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
Do("""CREATE TABLE wikipage (
    `id` integer NOT NULL DEFAULT '',
    `name` varchar(50) COLLATE utf8_general_ci DEFAULT NULL,
    `data` text COLLATE utf8_general_ci DEFAULT NULL,
    `modified` timestamp DEFAULT NULL,
     PRIMARY KEY(`id`),
     CONSTRAINT `wikipage_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict) CHARACTER SET=utf8 COLLATE=utf8_general_ci""")
