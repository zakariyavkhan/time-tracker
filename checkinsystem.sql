-- phpMyAdmin SQL Dump
-- version 5.0.4deb2
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Oct 22, 2022 at 02:35 PM
-- Server version: 10.5.12-MariaDB-0+deb11u1
-- PHP Version: 7.4.25
--
-- Creates checkinsystem DB for user 'sql_user'

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `checkinsystem`
--
CREATE DATABASE IF NOT EXISTS `checkinsystem` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `checkinsystem`;

-- --------------------------------------------------------

--
-- Table structure for table `attendance`
--

DROP TABLE IF EXISTS `attendance`;
CREATE TABLE `attendance` (
  `id` int(10) NOT NULL,
  `user_id` int(10) NOT NULL,
  `clock_in` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `name` varchar(255) CHARACTER SET utf8 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `attendance`
--

INSERT INTO `attendance` (`id`, `user_id`, `clock_in`, `name`) VALUES
(1, 3, '2022-10-21 14:51:18', 'Jessica'),
(2, 4, '2022-10-21 14:51:29', 'Erica'),
(3, 2, '2022-10-21 14:51:41', 'Jenny'),
(4, 1, '2022-10-21 15:35:36', 'Laura'),
(5, 1, '2022-10-21 18:05:48', 'Laura'),
(6, 3, '2022-10-21 19:14:20', 'Jessica'),
(7, 4, '2022-10-21 22:50:56', 'Erica'),
(8, 2, '2022-10-21 23:35:09', 'Jenny');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int(10) NOT NULL,
  `rfid_uid` bigint(255) NOT NULL,
  `name` varchar(255) CHARACTER SET utf8 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `rfid_uid`, `name`) VALUES
(1, 665213435956, 'Laura'),
(2, 662998909079, 'Jenny'),
(3, 629847701975, 'Jessica'),
(4, 176738237464, 'Erica'),

--
-- Indexes for dumped tables
--

--
-- Indexes for table `attendance`
--
ALTER TABLE `attendance`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `attendance`
--
ALTER TABLE `attendance`
  MODIFY `id` int(10) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1135;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(10) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

DELIMITER $$
--
-- Events
--
DROP EVENT `export_csv`$$
CREATE DEFINER=`sql_user`@`localhost` EVENT `export_csv` ON SCHEDULE EVERY 2 WEEK STARTS '2022-02-25 19:45:00' ON COMPLETION PRESERVE ENABLE DO BEGIN

    SET @stmt = concat("SELECT * FROM `attendance` WHERE DATE(attendance.clock_in) > DATE_SUB(NOW(), INTERVAL 2 WEEK) ORDER BY user_id, clock_in INTO OUTFILE '/var/tmp/timestamps",DATE_FORMAT(NOW(), '_%Y_%m_%d'),".csv' FIELDS ENCLOSED BY '""' TERMINATED BY ',' LINES TERMINATED BY '\n'");

    PREPARE cmd FROM @stmt;
    EXECUTE cmd;

END$$

DELIMITER ;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
