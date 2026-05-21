-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: derbi_pie_sql
-- ------------------------------------------------------
-- Server version	8.0.45-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `lex_master`
--

DROP TABLE IF EXISTS `lex_master`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lex_master` (
  `lemma_id` int NOT NULL,
  `lang` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `lemma` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `sense_num` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `page_num` int DEFAULT NULL,
  `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `orthography` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `ipa` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `pos` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `gender` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `stem` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `etymology` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `entry` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `entry_str` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `last_updated` datetime DEFAULT NULL,
  `editor` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `components` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gloss` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`lang`,`lemma_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `lex_senses`
--

DROP TABLE IF EXISTS `lex_senses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lex_senses` (
  `sense_id` int NOT NULL,
  `lang` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `lemma_id` int NOT NULL,
  `lemma` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sense_num` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `page_num` int DEFAULT NULL,
  `entry` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `entry_str` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `last_updated` datetime DEFAULT NULL,
  `editor` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `h_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parent_h_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gloss` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`lang`,`sense_id`),
  KEY `idx_lemma_id` (`lemma_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-15  8:27:40
