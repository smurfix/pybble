ALTER TABLE bindata
    ADD COLUMN `timestamp` timestamp NULL DEFAULT NULL;
ALTER TABLE usertracking
    DROP COLUMN `comment`;
