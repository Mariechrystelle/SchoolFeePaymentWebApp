-- School Fee Payment App database setup for XAMPP/phpMyAdmin
-- 1) Open phpMyAdmin
-- 2) Click SQL
-- 3) Paste this full script and run

CREATE DATABASE IF NOT EXISTS `HND26`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `HND26`;

-- Students
CREATE TABLE IF NOT EXISTS `students` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `full_name` VARCHAR(150) NOT NULL,
  `dob` DATE NOT NULL,
  `phone` VARCHAR(30) NOT NULL,
  `specialty` VARCHAR(120) NOT NULL,
  `program_level` VARCHAR(40) NOT NULL DEFAULT 'Level 1',
  `matricule` VARCHAR(80) NOT NULL DEFAULT 'undefined',
  `access_code` VARCHAR(12) NULL,
  `email` VARCHAR(191) NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `fee_total` DECIMAL(12,2) NULL,
  `paid_amount` DECIMAL(12,2) NOT NULL DEFAULT 0,
  `balance_amount` DECIMAL(12,2) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_students_email` (`email`),
  KEY `idx_students_matricule` (`matricule`)
);

-- Admins
CREATE TABLE IF NOT EXISTS `admins` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `full_name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(191) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_admins_email` (`email`)
);

-- Payments
CREATE TABLE IF NOT EXISTS `payments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `transaction_id` VARCHAR(64) NOT NULL,
  `amount` DECIMAL(12,2) NOT NULL,
  `purpose` VARCHAR(120) NOT NULL DEFAULT 'School Fees',
  `phone` VARCHAR(30) NOT NULL,
  `payment_method` VARCHAR(40) NULL,
  `academic_year` VARCHAR(20) NULL,
  `installment_label` VARCHAR(40) NULL,
  `fee_total` DECIMAL(12,2) NULL,
  `balance_after` DECIMAL(12,2) NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'Pending',
  `confirmation_code` VARCHAR(20) NOT NULL,
  `approved_at` DATETIME NULL,
  `approved_by` VARCHAR(150) NULL,
  `student_seen` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_payments_transaction_id` (`transaction_id`),
  KEY `idx_payments_student_id` (`student_id`),
  CONSTRAINT `fk_payments_student`
    FOREIGN KEY (`student_id`) REFERENCES `students` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- Departments
CREATE TABLE IF NOT EXISTS `departments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(120) NOT NULL UNIQUE,
  `code` VARCHAR(20) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Fee Items (Tuition, Exam, Registration, etc.)
CREATE TABLE IF NOT EXISTS `fee_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `department_id` INT NOT NULL,
  `program_level` VARCHAR(40) NOT NULL,
  `fee_type` VARCHAR(60) NOT NULL,
  `total_fee` DECIMAL(12,2) NOT NULL,
  `installment1` DECIMAL(12,2) NULL,
  `installment2` DECIMAL(12,2) NULL,
  `installment3` DECIMAL(12,2) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_fee_items_dept_level` (`department_id`, `program_level`),
  CONSTRAINT `fk_fee_items_department`
    FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- School finance summary
CREATE TABLE IF NOT EXISTS `school_finance` (
  `id` INT PRIMARY KEY,
  `total_collected` DECIMAL(14,2) NOT NULL DEFAULT 0,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO `school_finance` (`id`, `total_collected`)
SELECT 1, 0 WHERE NOT EXISTS (SELECT 1 FROM `school_finance` WHERE `id` = 1);

-- Admin audit log
CREATE TABLE IF NOT EXISTS `admin_audit_log` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `admin_id` INT NULL,
  `admin_name` VARCHAR(150) NULL,
  `action` VARCHAR(50) NOT NULL,
  `entity_type` VARCHAR(50) NOT NULL,
  `entity_id` VARCHAR(64) NOT NULL,
  `details` TEXT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Password reset tokens (student forgot-password flow)
CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `token` VARCHAR(80) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `used` TINYINT(1) NOT NULL DEFAULT 0,
  `used_at` DATETIME NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_password_reset_token` (`token`),
  KEY `idx_password_reset_student_id` (`student_id`),
  CONSTRAINT `fk_password_reset_student`
    FOREIGN KEY (`student_id`) REFERENCES `students` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- Contact messages (Contact Us form)
CREATE TABLE IF NOT EXISTS `contact_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `full_name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(191) NOT NULL,
  `subject` VARCHAR(200) NOT NULL,
  `message` TEXT NOT NULL,
  `overall_satisfaction` TINYINT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'Open',
  `admin_reply` TEXT NULL,
  `replied_by` VARCHAR(150) NULL,
  `replied_at` DATETIME NULL,
  `sender_ip` VARCHAR(45) NULL,
  `admin_seen` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Default admin account
-- Email: admin@school.com
-- Password: admin123
INSERT INTO `admins` (`full_name`, `email`, `password_hash`)
SELECT
  'System Admin',
  'admin@school.com',
  'scrypt:32768:8:1$prli44L291CJXXKg$0a914ec3786c4cf19df4a7e8f01e281bfb7935f36a87a38be8dfacd452ee682d0e6ce7803aa61c12fb87446390483588d98c47d4793759436e3ad62e2e794aaa'
WHERE NOT EXISTS (
  SELECT 1 FROM `admins` WHERE `email` = 'admin@school.com'
);
