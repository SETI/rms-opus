-- MySQL dump 10.13  Distrib 5.5.17, for osx10.6 (i386)
--
-- Host: localhost    Database: opus_hack
-- ------------------------------------------------------
-- Server version	5.5.17

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
-- Table structure for table `param_info`
--

DROP TABLE IF EXISTS `param_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `param_info` (
  `id` int(11) NOT NULL DEFAULT '0',
  `category_id` int(11) DEFAULT NULL,
  `name` varchar(87) NOT NULL,
  `type` varchar(18) NOT NULL,
  `length` int(11) NOT NULL,
  `slug` varchar(255) DEFAULT NULL,
  `post_length` int(11) NOT NULL,
  `form_type` varchar(21) DEFAULT NULL,
  `display` char(1) DEFAULT NULL,
  `rank` varchar(48) DEFAULT NULL,
  `disp_order` int(11) NOT NULL,
  `label` varchar(240) DEFAULT NULL,
  `intro` varchar(150) DEFAULT NULL,
  `category_name` varchar(150) NOT NULL,
  `display_results` tinyint(1) NOT NULL,
  `units` varchar(75) DEFAULT NULL,
  `tooltip` varchar(255) DEFAULT NULL,
  `dict_context` varchar(255) DEFAULT NULL,
  `dict_name` varchar(255) DEFAULT NULL,
  `checkbox_group_col_count` int(11) DEFAULT NULL,
  `special_query` varchar(15) DEFAULT NULL,
  `label_results` varchar(240) DEFAULT NULL,
  `onclick` varchar(75) DEFAULT NULL,
  `dict_more_info_context` varchar(255) DEFAULT NULL,
  `dict_more_info_name` varchar(255) DEFAULT NULL,
  `search_form` varchar(63) DEFAULT NULL,
  `mission` varchar(15) DEFAULT NULL,
  `instrument` varchar(15) DEFAULT NULL,
  `sub_heading` varchar(150) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-11-08 16:52:19
