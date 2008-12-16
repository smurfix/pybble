ALTER TABLE users
    ADD COLUMN `feed_age` tinyint(4) NOT NULL DEFAULT '0',
    ADD COLUMN `feed_pass` varchar(30) COLLATE utf8_general_ci NULL DEFAULT NULL;
