CREATE DATABASE IF NOT EXISTS smart_service;

CREATE USER IF NOT EXISTS 'smart_user'@'localhost'
IDENTIFIED BY 'smart_password';

GRANT ALL PRIVILEGES ON smart_service.* TO 'smart_user'@'localhost';

FLUSH PRIVILEGES;