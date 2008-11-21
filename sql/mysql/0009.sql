ALTER TABLE template_match
    ADD COLUMN `id` integer NOT NULL AUTO_INCREMENT DEFAULT NULL,
    ADD PRIMARY KEY(`id`);
ALTER TABLE templates
    ADD COLUMN `modified` timestamp NULL DEFAULT NULL;
