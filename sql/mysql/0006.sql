ALTER TABLE obj
    DROP FOREIGN KEY `None`,
    DROP FOREIGN KEY `None`,
    DROP FOREIGN KEY `None`;
ALTER TABLE site_users
    DROP FOREIGN KEY `None`,
    DROP FOREIGN KEY `None`;
ALTER TABLE sites
    DROP FOREIGN KEY `None`;
ALTER TABLE urls
    DROP FOREIGN KEY `None`;
ALTER TABLE users
    DROP FOREIGN KEY `None`,
    DROP FOREIGN KEY `None`,
    DROP FOREIGN KEY `None`;
ALTER TABLE site_users
    MODIFY COLUMN `site_id` integer NOT NULL DEFAULT '',
    MODIFY COLUMN `user_id` integer NOT NULL DEFAULT '',
    ADD UNIQUE KEY `x_1`(`site_id`,`user_id`);
ALTER TABLE sites
    MODIFY COLUMN `domain` varchar(100) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    MODIFY COLUMN `name` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    ADD UNIQUE KEY `x_4`(`name`),
    ADD UNIQUE KEY `x_3`(`domain`);
ALTER TABLE urls
    MODIFY COLUMN `uid` varchar(140) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    MODIFY COLUMN `target` varchar(500) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    MODIFY COLUMN `added` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
    MODIFY COLUMN `public` bool NOT NULL DEFAULT '',
    ADD UNIQUE KEY `x_2`(`uid`);
ALTER TABLE users
    MODIFY COLUMN `username` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    MODIFY COLUMN `password` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    MODIFY COLUMN `verified` bool NOT NULL DEFAULT '',
    MODIFY COLUMN `first_login` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
    MODIFY COLUMN `user_id` integer NOT NULL DEFAULT '',
    MODIFY COLUMN `obj_id` integer NOT NULL DEFAULT '';
ALTER TABLE obj
    ADD CONSTRAINT `obj_owner` FOREIGN KEY (`owner_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    ADD CONSTRAINT `obj_super` FOREIGN KEY (`superparent_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    ADD CONSTRAINT `obj_parent` FOREIGN KEY (`parent_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
ALTER TABLE site_users
    ADD CONSTRAINT `site_users_user` FOREIGN KEY (`user_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    ADD CONSTRAINT `site_users_site` FOREIGN KEY (`site_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
ALTER TABLE sites
    ADD CONSTRAINT `site_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
ALTER TABLE urls
    ADD CONSTRAINT `url_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
ALTER TABLE users
    ADD CONSTRAINT `permission_obj` FOREIGN KEY (`obj_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    ADD CONSTRAINT `user_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    ADD CONSTRAINT `permission_user` FOREIGN KEY (`user_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
