CREATE DATABASE IF NOT EXISTS minicloud;
USE minicloud;

CREATE TABLE IF NOT EXISTS notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO notes (title) VALUES
('Hello from MariaDB!'),
('MiniCloud database initialized'),
('Final Cloud project ready');

CREATE DATABASE IF NOT EXISTS studentdb;
USE studentdb;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(10) NOT NULL,
    fullname VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    major VARCHAR(50) NOT NULL
);

INSERT INTO students (student_id, fullname, dob, major) VALUES
('SV001', 'Ngo Nguyen Le Khanh', '2004-01-15', 'Computer Science'),
('SV002', 'Khong Duc Tuan', '2004-05-20', 'Information Technology'),
('SV003', 'Tran Luu Mai', '2004-09-10', 'Software Engineering');
