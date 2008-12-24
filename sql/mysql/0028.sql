CREATE TABLE renderer (
    `id` tinyint(1) NOT NULL AUTO_INCREMENT DEFAULT NULL,
    `name` varchar(30) COLLATE utf8_general_ci NOT NULL DEFAULT '',
    `cls` varchar(50) COLLATE utf8_general_ci NOT NULL DEFAULT '',
     PRIMARY KEY(`id`),
     UNIQUE KEY `x_28`(`name`),
     UNIQUE KEY `x_27`(`cls`)) CHARACTER SET=utf8 COLLATE=utf8_general_ci;
ALTER TABLE comment
    ADD COLUMN `renderer_id` tinyint(4) NULL DEFAULT NULL;
ALTER TABLE comment
    ADD CONSTRAINT `cmt_renderer` FOREIGN KEY (`renderer_id`) REFERENCES `renderer` (`id`) ON UPDATE cascade ON DELETE restrict;

INSERT INTO `renderer` VALUES(1,'markdown','pybble.render.render_markdown');
UPDATE comment SET renderer_id=1;
COMMIT;

