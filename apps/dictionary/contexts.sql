-- MySQL dump 10.13  Distrib 5.7.21, for Linux (x86_64)
--
-- Host: localhost    Database: dictionary
-- ------------------------------------------------------
-- Server version	5.7.21-0ubuntu0.16.04.1

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
-- Table structure for table `contexts`
--

DROP TABLE IF EXISTS `contexts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contexts` (
  `name` char(25) NOT NULL,
  `description` char(100) DEFAULT NULL,
  `parent` char(25) DEFAULT NULL,
  PRIMARY KEY (`name`),
  UNIQUE KEY `no` (`name`),
  UNIQUE KEY `contexts_name` (`name`),
  UNIQUE KEY `name` (`description`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contexts`
--

LOCK TABLES `contexts` WRITE;
/*!40000 ALTER TABLE `contexts` DISABLE KEYS */;
INSERT INTO `contexts` VALUES ('PSDD','NASA PDS Planetary Science Data Dictionary','NULL'),('COISS','Cassini Imaging Science Subsystem (ISS)','CASSINI'),('COVIMS','Cassini Visual and Infrared Mapping Spectrometer (VIMS)','CASSINI'),('GOSSI','Galileo Solid State Imaging (SSI)','GALILEO'),('NHLORRI','New Horizons Long-Range Reconnaissance Imager (LORRI)','NEWHORIZONS'),('COCIRS','Cassini Composite Infrared Spectrometer (CIRS)','CASSINI'),('HST','Hubble Space Telescope','OPUS_GENERAL'),('OPUS_GENERAL','OPUS General Constraints','PSDD'),('CASSINI','Cassini Mission','OPUS_GENERAL'),('RING_GEO','Ring Geometry','PSDD'),('SURFACE_GEO','Surface Geometry','PSDD'),('GALILEO','Galileo Mission','OPUS_GENERAL'),('VGISS','Voyager Imaging Science Subsystem (ISS)','VOYAGER'),('VOYAGER','Voyager Mission','OPUS_GENERAL'),('OPUS_WAVELENGTH','OPUS Wavelength Constraints','PSDD'),('OPUS_TYPE_IMAGE','OPUS Image Constraints','PSDD'),('COUVIS','Cassini UltraViolet Imaging Spectrograph (UVIS)','CASSINI'),('NEWHORIZONS','New Horizons Mission','OPUS_GENERAL'),('NHMVIC','New Horizons Multispectral Visible Imaging Camera (MVIC)','NEWHORIZONS');
/*!40000 ALTER TABLE `contexts` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-05-05 15:05:18
