-- MySQL dump 10.11
--
-- Host: intern.smurf.noris.de    Database: test_pybble
-- ------------------------------------------------------
-- Server version	5.0.51a-3ubuntu5.4-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bindata`
--

DROP TABLE IF EXISTS `bindata`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `bindata` (
  `id` int(11) NOT NULL,
  `mime_id` int(11) default NULL,
  `name` varchar(50) NOT NULL,
  `hash` tinyblob,
  `timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP,
  `storage_seq` int(11) NOT NULL auto_increment,
  `size` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `storage_seq` (`storage_seq`),
  UNIQUE KEY `hash` (`hash`(255)),
  KEY `bindata_mimeid` (`mime_id`),
  CONSTRAINT `bindata_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`),
  CONSTRAINT `bindata_mimeid` FOREIGN KEY (`mime_id`) REFERENCES `mimetype` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `books`
--

DROP TABLE IF EXISTS `books`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `books` (
  `id` int(11) NOT NULL,
  `title` varchar(250) default NULL,
  `author` varchar(250) default NULL,
  `upc` tinyblob,
  `info` text,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `upc` (`upc`(30)),
  CONSTRAINT `book_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `bookstore`
--

DROP TABLE IF EXISTS `bookstore`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `bookstore` (
  `id` int(11) NOT NULL,
  `name` varchar(250) default NULL,
  `info` varchar(250) default NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `bookstore_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `bookwant`
--

DROP TABLE IF EXISTS `bookwant`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `bookwant` (
  `id` int(11) NOT NULL,
  `requested` datetime default NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `bookwant_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `breadcrumbs`
--

DROP TABLE IF EXISTS `breadcrumbs`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `breadcrumbs` (
  `id` int(11) NOT NULL,
  `discr` tinyint(4) NOT NULL,
  `visited` timestamp NOT NULL default CURRENT_TIMESTAMP,
  `cur_visited` datetime default NULL,
  `last_visited` datetime default NULL,
  PRIMARY KEY  (`id`),
  KEY `breadcrumb_discr` (`discr`),
  CONSTRAINT `breadcrumb_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`),
  CONSTRAINT `breadcrumb_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `changes`
--

DROP TABLE IF EXISTS `changes`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `changes` (
  `id` int(11) NOT NULL,
  `timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `data` text,
  `comment` varchar(200) default NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `change_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `comment`
--

DROP TABLE IF EXISTS `comment`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `comment` (
  `id` int(11) NOT NULL,
  `name` varchar(250) default NULL,
  `data` text,
  `added` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `renderer_id` tinyint(4) default NULL,
  PRIMARY KEY  (`id`),
  KEY `cmt_renderer` (`renderer_id`),
  CONSTRAINT `cmt_renderer` FOREIGN KEY (`renderer_id`) REFERENCES `renderer` (`id`),
  CONSTRAINT `comment_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `deleted`
--

DROP TABLE IF EXISTS `deleted`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `deleted` (
  `id` int(11) NOT NULL,
  `comment` varchar(200) default NULL,
  `old_superparent_id` int(11) default NULL,
  `old_owner_id` int(11) default NULL,
  `timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`),
  KEY `delobj_owner` (`old_owner_id`),
  KEY `delobj_super` (`old_superparent_id`),
  CONSTRAINT `delete_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`),
  CONSTRAINT `delobj_owner` FOREIGN KEY (`old_owner_id`) REFERENCES `obj` (`id`),
  CONSTRAINT `delobj_super` FOREIGN KEY (`old_superparent_id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `demo`
--

DROP TABLE IF EXISTS `demo`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `demo` (
  `id` int(11) NOT NULL,
  `name` varchar(250) default NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `demo_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `discriminator`
--

DROP TABLE IF EXISTS `discriminator`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `discriminator` (
  `id` tinyint(1) NOT NULL auto_increment,
  `name` tinyblob,
  `display_name` varchar(50) default NULL,
  `infotext` varchar(250) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`(255))
) ENGINE=InnoDB AUTO_INCREMENT=108 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `groupmembers`
--

DROP TABLE IF EXISTS `groupmembers`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `groupmembers` (
  `id` int(11) NOT NULL,
  `excluded` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `member_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `groups`
--

DROP TABLE IF EXISTS `groups`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `groups` (
  `id` int(11) NOT NULL,
  `name` varchar(30) default NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `group_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `mimeext`
--

DROP TABLE IF EXISTS `mimeext`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `mimeext` (
  `id` int(11) NOT NULL auto_increment,
  `mime_id` int(11) default NULL,
  `ext` varchar(10) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `ext` (`ext`),
  KEY `mimetype_id` (`mime_id`),
  CONSTRAINT `mimetype_id` FOREIGN KEY (`mime_id`) REFERENCES `mimetype` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `mimetype`
--

DROP TABLE IF EXISTS `mimetype`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `mimetype` (
  `id` int(11) NOT NULL auto_increment,
  `name` varchar(30) NOT NULL,
  `typ` tinyblob,
  `subtyp` tinyblob,
  `ext` varchar(15) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `obj`
--

DROP TABLE IF EXISTS `obj`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `obj` (
  `id` int(11) NOT NULL auto_increment,
  `discriminator` tinyint(4) default NULL,
  `owner_id` int(11) default NULL,
  `parent_id` int(11) default NULL,
  `superparent_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  KEY `obj_discr` (`discriminator`),
  KEY `obj_owner` (`owner_id`),
  KEY `obj_parent` (`parent_id`),
  KEY `obj_super` (`superparent_id`),
  CONSTRAINT `obj_discr` FOREIGN KEY (`discriminator`) REFERENCES `discriminator` (`id`),
  CONSTRAINT `obj_owner` FOREIGN KEY (`owner_id`) REFERENCES `obj` (`id`),
  CONSTRAINT `obj_parent` FOREIGN KEY (`parent_id`) REFERENCES `obj` (`id`),
  CONSTRAINT `obj_super` FOREIGN KEY (`superparent_id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=352 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `permissions`
--

DROP TABLE IF EXISTS `permissions`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `permissions` (
  `id` int(11) NOT NULL,
  `right` int(11) NOT NULL,
  `inherit` tinyint(1) default NULL,
  `discr` tinyint(4) NOT NULL,
  `new_discr` tinyint(4) default NULL,
  PRIMARY KEY  (`id`),
  KEY `permission_discr` (`discr`),
  KEY `permission_new_discr` (`new_discr`),
  CONSTRAINT `permission_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`),
  CONSTRAINT `permission_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`),
  CONSTRAINT `permission_new_discr` FOREIGN KEY (`new_discr`) REFERENCES `discriminator` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `renderer`
--

DROP TABLE IF EXISTS `renderer`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `renderer` (
  `id` tinyint(1) NOT NULL auto_increment,
  `name` varchar(30) NOT NULL,
  `cls` varchar(50) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `cls` (`cls`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `sites`
--

DROP TABLE IF EXISTS `sites`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `sites` (
  `id` int(11) NOT NULL,
  `domain` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  `tracked` datetime NOT NULL,
  `storage_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `domain` (`domain`),
  UNIQUE KEY `name` (`name`),
  KEY `site_storage` (`storage_id`),
  CONSTRAINT `site_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`),
  CONSTRAINT `site_storage` FOREIGN KEY (`storage_id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `staticfile`
--

DROP TABLE IF EXISTS `staticfile`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `staticfile` (
  `id` int(11) NOT NULL,
  `path` varchar(200) NOT NULL,
  `modified` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`),
  CONSTRAINT `staticfile_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `storage`
--

DROP TABLE IF EXISTS `storage`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `storage` (
  `id` int(11) NOT NULL,
  `name` varchar(250) NOT NULL,
  `path` varchar(250) NOT NULL,
  `url` varchar(250) NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `url` (`url`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `path` (`path`),
  CONSTRAINT `storage_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `template_match`
--

DROP TABLE IF EXISTS `template_match`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `template_match` (
  `id` int(11) NOT NULL,
  `data` text,
  `modified` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `discr` tinyint(4) NOT NULL,
  `detail` tinyint(1) NOT NULL,
  `inherit` tinyint(1) default NULL,
  PRIMARY KEY  (`id`),
  KEY `templatematch_discr` (`discr`),
  CONSTRAINT `templatematch_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`),
  CONSTRAINT `template_match_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `templates`
--

DROP TABLE IF EXISTS `templates`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `templates` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `data` text,
  `modified` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`),
  CONSTRAINT `template_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `tracking`
--

DROP TABLE IF EXISTS `tracking`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `tracking` (
  `id` int(11) NOT NULL,
  `timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  PRIMARY KEY  (`id`),
  CONSTRAINT `tracker_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(30) NOT NULL,
  `first_name` varchar(30) default NULL,
  `last_name` varchar(30) default NULL,
  `email` varchar(200) NOT NULL,
  `password` varchar(30) NOT NULL,
  `first_login` datetime NOT NULL,
  `last_login` datetime default NULL,
  `cur_login` datetime default NULL,
  `feed_age` tinyint(4) NOT NULL,
  `feed_pass` varchar(30) default NULL,
  `feed_read` datetime default NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `user_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `usertracking`
--

DROP TABLE IF EXISTS `usertracking`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `usertracking` (
  `id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `usertracker_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `verein`
--

DROP TABLE IF EXISTS `verein`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `verein` (
  `id` int(11) NOT NULL,
  `name` varchar(250) default NULL,
  `database` varchar(30) default NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `verein_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `verein_member`
--

DROP TABLE IF EXISTS `verein_member`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `verein_member` (
  `id` int(11) NOT NULL,
  `mitglied_id` int(11) default NULL,
  `aktiv` tinyint(1) default NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `vereinmember_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `vereinacct`
--

DROP TABLE IF EXISTS `vereinacct`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `vereinacct` (
  `id` int(11) NOT NULL,
  `accountdb` varchar(30) default NULL,
  `accountnr` int(11) default NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `vereinacct_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `verifierbase`
--

DROP TABLE IF EXISTS `verifierbase`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `verifierbase` (
  `id` tinyint(1) NOT NULL auto_increment,
  `name` varchar(30) NOT NULL,
  `cls` tinyblob,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `cls` (`cls`(255))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `verifiers`
--

DROP TABLE IF EXISTS `verifiers`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `verifiers` (
  `id` int(11) NOT NULL,
  `base_id` tinyint(4) default NULL,
  `code` tinyblob,
  `added` datetime NOT NULL,
  `repeated` datetime default NULL,
  `timeout` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `code` (`code`(255)),
  KEY `verifier_base` (`base_id`),
  CONSTRAINT `verifier_base` FOREIGN KEY (`base_id`) REFERENCES `verifierbase` (`id`),
  CONSTRAINT `verifier_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `wanttracking`
--

DROP TABLE IF EXISTS `wanttracking`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `wanttracking` (
  `id` int(11) NOT NULL,
  `discr` tinyint(4) default NULL,
  `email` tinyint(1) NOT NULL,
  `track_new` tinyint(1) NOT NULL,
  `track_mod` tinyint(1) NOT NULL,
  `track_del` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `wanttracking_discr` (`discr`),
  CONSTRAINT `wanttracking_discr` FOREIGN KEY (`discr`) REFERENCES `discriminator` (`id`),
  CONSTRAINT `wanttracking_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `wikipage`
--

DROP TABLE IF EXISTS `wikipage`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `wikipage` (
  `id` int(11) NOT NULL,
  `name` varchar(50) default NULL,
  `data` text,
  `modified` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `mainpage` tinyint(1) NOT NULL,
  PRIMARY KEY  (`id`),
  CONSTRAINT `wikipage_id` FOREIGN KEY (`id`) REFERENCES `obj` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2009-07-13  6:39:15
