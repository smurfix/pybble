#FK obj_discr fields: ['discr'] ['discriminator']
ALTER TABLE permissions
    DROP FOREIGN KEY `permission_obj`,
    DROP FOREIGN KEY `obj_discr`,
    DROP FOREIGN KEY `permission_user`;
#FK templatematch_discr fields: ['discr'] ['discriminator']
ALTER TABLE template_match
    DROP FOREIGN KEY `templatematch_discr`;
ALTER TABLE permissions
    ADD COLUMN `discr` tinyint(4) NOT NULL DEFAULT '0',
    MODIFY COLUMN `id` integer NOT NULL DEFAULT '',
    MODIFY COLUMN `right` integer NOT NULL DEFAULT '',
    DROP COLUMN `user_id`,
    DROP COLUMN `obj_id`,
    DROP COLUMN `discriminator`;
ALTER TABLE template_match
    ADD COLUMN `discr` tinyint(4) NOT NULL DEFAULT '0',
    DROP COLUMN `discriminator`;
ALTER TABLE permissions
    ADD CONSTRAINT `obj_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict,
    ADD CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
ALTER TABLE template_match
    ADD CONSTRAINT `templatematch_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict;
DROP TABLE `urls`;
