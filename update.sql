-- Sometime the database scheme from fedocal is changing
-- This file tries to track down these changes allowing you to keep
-- you database structure.
-- However, this file is intended temporarily for development purposes
-- until a better solution can be found (such as using Alembic).

-- Use at your own risk -- Data may be lost

USE fedocal;

-- 2012/11/01
ALTER TABLE `calendars` ADD calendar_regional_meetings tinyint(1) DEFAULT NULL;
ALTER TABLE `meetings` ADD meeting_region varchar(10) DEFAULT NULL;

-- 2012/11/05 - Change the Meetings table and drop the recursion table
ALTER TABLE `meetings` ADD recursion_frequency Integer DEFAULT NULL;
ALTER TABLE `meetings` ADD recursion_ends Date DEFAULT NULL;

-- the foreign key name might change, see "SHOW CREATE TABLE meetings;"
-- to be sure
ALTER TABLE `meetings` DROP FOREIGN KEY `meetings_ibfk_3`;
ALTER TABLE `meetings` DROP COLUMN `recursion_id`;

DROP TABLE `recursivity`;


-- Check the changes:
SHOW TABLES ;
SHOW CREATE TABLE meetings;
DESCRIBE meetings;
