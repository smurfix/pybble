ALTER TABLE groupmembers
    DROP FOREIGN KEY `member_group`,
    DROP FOREIGN KEY `member_user`;
ALTER TABLE template_match
    DROP FOREIGN KEY `obj_templates_obj`,
    DROP FOREIGN KEY `obj_templates_template`;
ALTER TABLE groupmembers
    MODIFY COLUMN `id` integer NOT NULL DEFAULT '',
    DROP COLUMN `user_id`,
    DROP COLUMN `group_id`;
ALTER TABLE permissions
    ADD COLUMN `new_discr` tinyint(4) NULL DEFAULT NULL;
ALTER TABLE template_match
    ADD COLUMN `detail` tinyint(1) NOT NULL DEFAULT '0',
    MODIFY COLUMN `id` integer NOT NULL DEFAULT '',
    DROP COLUMN `obj_id`,
    DROP COLUMN `template_id`,
    DROP COLUMN `type`;
ALTER TABLE groupmembers
    ADD CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
ALTER TABLE permissions
    ADD CONSTRAINT `obj_new_discr` FOREIGN KEY (`new_discr`) REFERENCES `discriminator` (`id`) ON UPDATE cascade ON DELETE restrict;
ALTER TABLE template_match
    ADD CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
