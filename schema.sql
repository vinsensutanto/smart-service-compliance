CREATE DATABASE ssca;

CREATE TABLE roles(
    role_id VARCHAR(6) PRIMARY KEY,
    role_name VARCHAR(100),
    CONSTRAINT chk_role_id CHECK(role_id REGEXP '^RL[0-9]{4}$')
);

CREATE TABLE workstations(
    workstation_id VARCHAR(6) PRIMARY KEY,
    pc_id VARCHAR(6),
    rpi_id VARCHAR(6),
    location VARCHAR(100),
    is_active BOOLEAN,
    CONSTRAINT chk_workstation_id CHECK(workstation_id REGEXP '^WS[0-9]{4}$'),
    CONSTRAINT chk_pc_id CHECK(pc_id REGEXP '^PC[0-9]{4}$'),
    CONSTRAINT chk_rpi_id CHECK(rpi_id REGEXP '^RP[0-9]{4}$')
);


CREATE TABLE sop_services (
    service_id VARCHAR(6) PRIMARY KEY,
    service_name VARCHAR(255),
    CONSTRAINT chk_service_id CHECK(service_id REGEXP '^SV[0-9]{4}$')
);

CREATE TABLE users (
    user_id VARCHAR(6) PRIMARY KEY,
    role_id VARCHAR(6),
    name VARCHAR(255),
    email VARCHAR(255),
    email_verified_at TIMESTAMP NULL,
    password VARCHAR(255),
    remember_token VARCHAR(100),
    is_active BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_user_id CHECK(user_id REGEXP '^US[0-9]{4}$'),
    CONSTRAINT fk_role_id FOREIGN KEY (role_id) REFERENCES roles(role_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE sop_steps (
    step_id VARCHAR(6) PRIMARY KEY,
    service_id VARCHAR(6),
    step_number INT,
    step_description VARCHAR(255),
    CONSTRAINT chk_step_id CHECK(step_id REGEXP '^ST[0-9]{4}$'),
    CONSTRAINT fk_service_id FOREIGN KEY (service_id) REFERENCES sop_services(service_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE service_records (
    service_record_id VARCHAR(6) PRIMARY KEY,
    workstation_id VARCHAR(6),
    user_id VARCHAR(6),
    service_detected VARCHAR(255),
    confidence FLOAT(3,2),
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    duration INT,
    text LONGTEXT,
    is_normal_flow BOOLEAN,
    reason VARCHAR(255),
    audio_path VARCHAR(255),
    CONSTRAINT chk_service_record_id CHECK(service_record_id REGEXP '^SR[0-9]{4}$'),
    CONSTRAINT fk_workstation_id FOREIGN KEY (workstation_id) REFERENCES workstations(workstation_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE service_chunks (
    chunk_id VARCHAR(6) PRIMARY KEY,
    service_record_id VARCHAR(6),
    text_chunk VARCHAR(255),
    created_at TIMESTAMP NULL,
    CONSTRAINT chk_chunk_id CHECK(chunk_id REGEXP '^CU[0-9]{4}$'),
    CONSTRAINT fk_service_record_id_1 FOREIGN KEY (service_record_id) REFERENCES service_records(service_record_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE service_checklists (
    checklist_id VARCHAR(6) PRIMARY KEY,
    service_record_id VARCHAR(6),
    step_id VARCHAR(6),
    is_checked BOOLEAN,
    checked_at TIMESTAMP NULL,
    CONSTRAINT chk_checklist_id CHECK(checklist_id REGEXP '^CE[0-9]{4}$'),
    CONSTRAINT fk_service_record_id_2 FOREIGN KEY (service_record_id) REFERENCES service_records(service_record_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_step_id FOREIGN KEY (step_id) REFERENCES sop_steps(step_id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- -- MySQL dump 10.13  Distrib 8.0.44, for Linux (x86_64)
-- --
-- -- Host: localhost    Database: smart_service
-- -- ------------------------------------------------------
-- -- Server version	8.0.44-0ubuntu0.24.04.2

-- /*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
-- /*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
-- /*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
-- /*!50503 SET NAMES utf8mb4 */;
-- /*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
-- /*!40103 SET TIME_ZONE='+00:00' */;
-- /*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
-- /*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
-- /*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
-- /*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- --
-- -- Table structure for table `roles`
-- --

-- DROP TABLE IF EXISTS `roles`;
-- /*!40101 SET @saved_cs_client     = @@character_set_client */;
-- /*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `roles` (
--   `role_id` varchar(6) NOT NULL,
--   `role_name` varchar(100) NOT NULL,
--   PRIMARY KEY (`role_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- /*!40101 SET character_set_client = @saved_cs_client */;

-- --
-- -- Table structure for table `service_checklists`
-- --

-- DROP TABLE IF EXISTS `service_checklists`;
-- /*!40101 SET @saved_cs_client     = @@character_set_client */;
-- /*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `service_checklists` (
--   `checklist_id` varchar(6) NOT NULL,
--   `service_record_id` varchar(6) DEFAULT NULL,
--   `step_id` varchar(6) DEFAULT NULL,
--   `is_checked` tinyint(1) DEFAULT '0',
--   `checked_at` datetime DEFAULT NULL,
--   PRIMARY KEY (`checklist_id`),
--   KEY `service_record_id` (`service_record_id`),
--   KEY `step_id` (`step_id`),
--   CONSTRAINT `service_checklists_ibfk_1` FOREIGN KEY (`service_record_id`) REFERENCES `service_records` (`service_record_id`),
--   CONSTRAINT `service_checklists_ibfk_2` FOREIGN KEY (`step_id`) REFERENCES `sop_steps` (`step_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- /*!40101 SET character_set_client = @saved_cs_client */;

-- --
-- -- Table structure for table `service_chunks`
-- --

-- DROP TABLE IF EXISTS `service_chunks`;
-- /*!40101 SET @saved_cs_client     = @@character_set_client */;
-- /*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `service_chunks` (
--   `chunk_id` varchar(6) NOT NULL,
--   `service_record_id` varchar(6) DEFAULT NULL,
--   `text_chunk` text,
--   `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
--   PRIMARY KEY (`chunk_id`),
--   KEY `service_record_id` (`service_record_id`),
--   CONSTRAINT `service_chunks_ibfk_1` FOREIGN KEY (`service_record_id`) REFERENCES `service_records` (`service_record_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- /*!40101 SET character_set_client = @saved_cs_client */;

-- --
-- -- Table structure for table `service_records`
-- --

-- DROP TABLE IF EXISTS `service_records`;
-- /*!40101 SET @saved_cs_client     = @@character_set_client */;
-- /*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `service_records` (
--   `service_record_id` varchar(6) NOT NULL,
--   `workstation_id` varchar(6) DEFAULT NULL,
--   `user_id` varchar(6) DEFAULT NULL,
--   `service_detected` varchar(255) DEFAULT NULL,
--   `confidence` decimal(4,3) DEFAULT NULL,
--   `start_time` datetime DEFAULT NULL,
--   `end_time` datetime DEFAULT NULL,
--   `duration` int DEFAULT NULL,
--   `text` longtext,
--   `is_normal_flow` tinyint(1) DEFAULT NULL,
--   `reason` varchar(255) DEFAULT NULL,
--   `audio_path` varchar(255) DEFAULT NULL,
--   PRIMARY KEY (`service_record_id`),
--   KEY `workstation_id` (`workstation_id`),
--   KEY `user_id` (`user_id`),
--   CONSTRAINT `service_records_ibfk_1` FOREIGN KEY (`workstation_id`) REFERENCES `workstations` (`workstation_id`),
--   CONSTRAINT `service_records_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- /*!40101 SET character_set_client = @saved_cs_client */;

-- --
-- -- Table structure for table `sop_services`
-- --

-- DROP TABLE IF EXISTS `sop_services`;
-- /*!40101 SET @saved_cs_client     = @@character_set_client */;
-- /*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `sop_services` (
--   `service_id` varchar(6) NOT NULL,
--   `service_name` varchar(255) NOT NULL,
--   PRIMARY KEY (`service_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- /*!40101 SET character_set_client = @saved_cs_client */;

-- --
-- -- Table structure for table `sop_steps`
-- --

-- DROP TABLE IF EXISTS `sop_steps`;
-- /*!40101 SET @saved_cs_client     = @@character_set_client */;
-- /*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `sop_steps` (
--   `step_id` varchar(6) NOT NULL,
--   `service_id` varchar(6) DEFAULT NULL,
--   `step_number` int DEFAULT NULL,
--   `step_description` varchar(255) DEFAULT NULL,
--   PRIMARY KEY (`step_id`),
--   KEY `service_id` (`service_id`),
--   CONSTRAINT `sop_steps_ibfk_1` FOREIGN KEY (`service_id`) REFERENCES `sop_services` (`service_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- /*!40101 SET character_set_client = @saved_cs_client */;

-- --
-- -- Table structure for table `users`
-- --

-- DROP TABLE IF EXISTS `users`;
-- /*!40101 SET @saved_cs_client     = @@character_set_client */;
-- /*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `users` (
--   `user_id` varchar(6) NOT NULL,
--   `role_id` varchar(6) DEFAULT NULL,
--   `name` varchar(255) DEFAULT NULL,
--   `email` varchar(255) DEFAULT NULL,
--   `email_verified_at` datetime DEFAULT NULL,
--   `password` varchar(255) DEFAULT NULL,
--   `remember_token` varchar(100) DEFAULT NULL,
--   `is_active` tinyint(1) DEFAULT '1',
--   `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
--   `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--   PRIMARY KEY (`user_id`),
--   UNIQUE KEY `email` (`email`),
--   KEY `role_id` (`role_id`),
--   CONSTRAINT `users_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- /*!40101 SET character_set_client = @saved_cs_client */;

-- --
-- -- Table structure for table `workstations`
-- --

-- DROP TABLE IF EXISTS `workstations`;
-- /*!40101 SET @saved_cs_client     = @@character_set_client */;
-- /*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `workstations` (
--   `workstation_id` varchar(6) NOT NULL,
--   `pc_id` varchar(6) DEFAULT NULL,
--   `rpi_id` varchar(6) DEFAULT NULL,
--   `location` varchar(100) DEFAULT NULL,
--   `is_active` tinyint(1) DEFAULT '1',
--   PRIMARY KEY (`workstation_id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
-- /*!40101 SET character_set_client = @saved_cs_client */;
-- /*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

-- /*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
-- /*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
-- /*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
-- /*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
-- /*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
-- /*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
-- /*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- -- Dump completed on 2025-12-22 21:25:17
