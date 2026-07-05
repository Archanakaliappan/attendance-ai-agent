-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: attendancejframebd
-- ------------------------------------------------------
-- Server version	8.0.42

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
-- Table structure for table `agent_absent_log`
--

DROP TABLE IF EXISTS `agent_absent_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_absent_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userid` int NOT NULL,
  `absent_date` date NOT NULL,
  `marked_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_date` (`userid`,`absent_date`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agent_absent_log`
--

LOCK TABLES `agent_absent_log` WRITE;
/*!40000 ALTER TABLE `agent_absent_log` DISABLE KEYS */;
INSERT INTO `agent_absent_log` VALUES (1,2,'2026-07-04','2026-07-04 23:20:38'),(2,3,'2026-07-04','2026-07-04 23:20:38'),(3,2,'2026-07-05','2026-07-05 09:52:56'),(4,3,'2026-07-05','2026-07-05 09:52:56'),(5,103,'2026-07-05','2026-07-05 09:52:56');
/*!40000 ALTER TABLE `agent_absent_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agent_late_explanations`
--

DROP TABLE IF EXISTS `agent_late_explanations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_late_explanations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `reason_raw` text NOT NULL,
  `letter_generated` text NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `student_id` (`student_id`),
  CONSTRAINT `agent_late_explanations_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `userdetails` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agent_late_explanations`
--

LOCK TABLES `agent_late_explanations` WRITE;
/*!40000 ALTER TABLE `agent_late_explanations` DISABLE KEYS */;
INSERT INTO `agent_late_explanations` VALUES (1,102,'Bus breakdown','Dear Sir/Madam,\n\nPlease accept my sincere apologies for my tardiness to class/work this morning. I was unfortunately delayed due to an unexpected bus breakdown, which significantly disrupted my commute. I understand the importance of punctuality and regret any inconvenience my late arrival may have caused. I will ensure I catch up on anything missed immediately.\n\nSincerely,\nJane Late','2026-07-04 19:48:19'),(2,102,'Bus breakdown','Dear Sir/Madam,\n\nPlease accept my sincerest apologies for my late arrival to class/work today. I experienced an unexpected bus breakdown on my route, which unfortunately caused a significant delay in my commute. I understand the importance of punctuality and deeply regret any inconvenience or disruption my tardiness may have caused. I will ensure I catch up on anything missed as quickly as possible.\n\nSincerely,\nJane Late','2026-07-05 04:22:46');
/*!40000 ALTER TABLE `agent_late_explanations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agent_leave_requests`
--

DROP TABLE IF EXISTS `agent_leave_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_leave_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `student_id` int NOT NULL,
  `reason_raw` text NOT NULL,
  `letter_generated` text NOT NULL,
  `status` varchar(20) DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `student_id` (`student_id`),
  CONSTRAINT `agent_leave_requests_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `userdetails` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agent_leave_requests`
--

LOCK TABLES `agent_leave_requests` WRITE;
/*!40000 ALTER TABLE `agent_leave_requests` DISABLE KEYS */;
INSERT INTO `agent_leave_requests` VALUES (1,103,'I have fever today','Dear Sir/Madam,\n\nPlease accept this letter as formal notification that I, Bob Absent, am unable to attend class due to the following reason: I have fever today.\n\nSincerely,\nBob Absent','approved','2026-07-04 19:08:04'),(2,103,'I have fever today','Dear Sir/Madam,\n\nI am writing to inform you that I will be unable to attend classes today due to fever. I apologize for any inconvenience this may cause.\n\nThank you for your understanding.\n\nSincerely,\nBob Absent','rejected','2026-07-04 19:08:56'),(3,103,'I have fever today','Dear Sir/Madam,\n\nI am writing to inform you that I will be unable to attend classes today due to a fever. I kindly request a leave of absence for the day.\n\nThank you for your understanding.\n\nSincerely,\nBob Absent','approved','2026-07-04 19:30:27'),(4,103,'I have fever today','Dear Sir/Madam,\n\nI am writing to inform you that I will be unable to attend classes today, as I am suffering from a fever. I apologize for any inconvenience this may cause.\n\nSincerely,\nBob Absent','pending','2026-07-04 19:53:48'),(5,103,'I have fever today','Dear Sir/Madam,\n\nI am writing to inform you that I will be unable to attend classes today, as I am suffering from a fever. I will endeavor to catch up on any missed work as soon as I recover.\n\nThank you for your understanding.\n\nSincerely,\nBob Absent','pending','2026-07-05 04:22:22');
/*!40000 ALTER TABLE `agent_leave_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agent_notification_log`
--

DROP TABLE IF EXISTS `agent_notification_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agent_notification_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userid` int NOT NULL,
  `notification_date` date NOT NULL,
  `reminder_type` varchar(20) NOT NULL,
  `sent_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_date_type` (`userid`,`notification_date`,`reminder_type`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agent_notification_log`
--

LOCK TABLES `agent_notification_log` WRITE;
/*!40000 ALTER TABLE `agent_notification_log` DISABLE KEYS */;
INSERT INTO `agent_notification_log` VALUES (1,2,'2026-07-04','first','2026-07-04 23:20:38'),(2,3,'2026-07-04','first','2026-07-04 23:20:38'),(3,2,'2026-07-04','second','2026-07-04 23:20:38'),(4,3,'2026-07-04','second','2026-07-04 23:20:38'),(6,2,'2026-07-05','first','2026-07-05 09:43:09'),(7,3,'2026-07-05','first','2026-07-05 09:43:09'),(8,103,'2026-07-05','first','2026-07-05 09:43:09'),(9,0,'2026-07-05','admin_summary','2026-07-05 09:52:56'),(10,2,'2026-07-05','second','2026-07-05 10:23:27'),(11,3,'2026-07-05','second','2026-07-05 10:23:27'),(12,103,'2026-07-05','second','2026-07-05 10:23:27');
/*!40000 ALTER TABLE `agent_notification_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userattendance`
--

DROP TABLE IF EXISTS `userattendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `userattendance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userid` int NOT NULL,
  `attendancedate` date NOT NULL,
  `checkin` datetime DEFAULT NULL,
  `checkout` datetime DEFAULT NULL,
  `workduration` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `userid` (`userid`),
  CONSTRAINT `userattendance_ibfk_1` FOREIGN KEY (`userid`) REFERENCES `userdetails` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userattendance`
--

LOCK TABLES `userattendance` WRITE;
/*!40000 ALTER TABLE `userattendance` DISABLE KEYS */;
INSERT INTO `userattendance` VALUES (2,101,'2026-07-05','2026-07-05 09:15:00',NULL,NULL),(3,102,'2026-07-05','2026-07-05 09:50:00',NULL,NULL);
/*!40000 ALTER TABLE `userattendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userdetails`
--

DROP TABLE IF EXISTS `userdetails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `userdetails` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `gender` varchar(50) NOT NULL,
  `email` varchar(255) NOT NULL,
  `contact` varchar(20) NOT NULL,
  `address` varchar(500) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `uniqueregid` varchar(100) NOT NULL,
  `imagename` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userdetails`
--

LOCK TABLES `userdetails` WRITE;
/*!40000 ALTER TABLE `userdetails` DISABLE KEYS */;
INSERT INTO `userdetails` VALUES (2,'arch','Female','aa@gmail.com','23451','1asdt','sss','aaa','823717101250082371710129008237171013000','aa@gmail.com png'),(3,'Archana','Female','archanakkalaiappan@gmail.com','90748','2','tn','tn','113988860049600113988860050100113988860050300','archanakkalaiappan@gmail.com png'),(101,'John OnTime','Male','john.ontime@example.com','1234567890','123 St','StateA','CountryA','REG101','john.png'),(102,'Jane Late','Female','jane.late@example.com','0987654321','456 Rd','StateB','CountryB','REG102','jane.png'),(103,'Bob Absent','Male','bob.absent@example.com','1122334455','789 Ave','StateC','CountryC','REG103','bob.png');
/*!40000 ALTER TABLE `userdetails` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-05 10:47:24
