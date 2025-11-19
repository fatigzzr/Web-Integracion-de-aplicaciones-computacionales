/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.5.27-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: Images
-- ------------------------------------------------------
-- Server version	10.5.27-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 
*/;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `images` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `filename` varchar(512) NOT NULL,
  `uploaded_at` datetime NOT NULL DEFAULT current_timestamp(),
  `size_bytes` bigint(20) unsigned NOT NULL,
  `mime_type` varchar(128) NOT NULL,
  `signed_url` text NOT NULL,
  PRIMARY KEY (`id`),
  KEY `uploaded_at` (`uploaded_at`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_c
i;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `images`
--

LOCK TABLES `images` WRITE;
/*!40000 ALTER TABLE `images` DISABLE KEYS */;
INSERT INTO `images` VALUES (3,'images.jpeg','2025-11-05 21:32:34',11154,'image/
jpeg','https://storage.googleapis.com/fati_bucket/images.jpeg?Expires=1762381954
&GoogleAccessId=715386068770-compute%40developer.gserviceaccount.com&Signature=G
ScGMm6w3uZZXh5ijQO3wpvvEP8pnuttD%2BSEe6cOaJ1VlYpT4DHdosQNIObnD%2FFSrgW09oyoYcY%2
B4nklAXV%2BXECTtDyPho5mjBO1EtZOHycDjZfG%2FhrJ4TYjtUzxzwARdBjC0gWC%2BSNORmx68nW3g
cCeFFWetupGy%2B8D2rJr%2BHjflAyC2DWyTvijmltUXh2zedxsYPITu6i%2F4p2omOZxYg7q%2B1vgS
K%2B55AiSu6cUux1WfxiLW6jIi5P5vYAuM7e1%2BLtELmphwqaZMZAySIKVsLC3UXnkV7DngAyAM5QdD
x8G%2BSD96E%2FeEthH5BCpf8rZXnvCgss4Ogp0JK8DHUZh6Q%3D%3D');
/*!40000 ALTER TABLE `images` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-19 15:59:34