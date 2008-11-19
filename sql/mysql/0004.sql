#FK None fields: ['parent_id'] ['site']
#FK None fields: ['parent_id'] ['owner']
#FK None fields: ['parent_id'] ['superowner']
ALTER TABLE obj
    DROP FOREIGN KEY `None`,
    DROP FOREIGN KEY `None`,
    DROP FOREIGN KEY `None`;
ALTER TABLE obj
    ADD COLUMN `owner_id` integer NULL DEFAULT NULL,
    ADD COLUMN `parent_id` integer NULL DEFAULT NULL,
    ADD COLUMN `superparent_id` integer NULL DEFAULT NULL,
    DROP COLUMN `owner`,
    DROP COLUMN `superowner`,
    DROP COLUMN `site`;
#FK None fields: ['owner_id'] ['site']
#FK None fields: ['owner_id'] ['site']
#FK None fields: ['superparent_id'] ['site']
#FK None fields: ['superparent_id'] ['site']
#FK None fields: ['parent_id'] ['site']
#FK None fields: ['parent_id'] ['site']
ALTER TABLE obj
    DROP CONSTRAINT `None`,
    ADD FOREIGN KEY (`owner_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    DROP CONSTRAINT `None`,
    ADD FOREIGN KEY (`superparent_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    DROP CONSTRAINT `None`,
    ADD FOREIGN KEY (`parent_id`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
