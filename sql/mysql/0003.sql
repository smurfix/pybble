ALTER TABLE obj
    ADD COLUMN `owner` integer NULL DEFAULT NULL,
    ADD COLUMN `superowner` integer NULL DEFAULT NULL,
    ADD COLUMN `site` integer NULL DEFAULT NULL;
ALTER TABLE obj
    ADD FOREIGN KEY (`site`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    ADD FOREIGN KEY (`owner`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict,
    ADD FOREIGN KEY (`superowner`) REFERENCES `obj` (`id`) ON UPDATE cascade ON DELETE restrict;
