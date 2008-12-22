ALTER TABLE template_match
    ADD COLUMN `data` text COLLATE utf8_general_ci NULL DEFAULT NULL,
    ADD COLUMN `modified` timestamp NULL DEFAULT NULL;
