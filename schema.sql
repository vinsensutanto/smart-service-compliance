-- Drop tables if they exist (in order to avoid FK conflicts)
DROP TABLE IF EXISTS service_checklists;
DROP TABLE IF EXISTS service_chunks;
DROP TABLE IF EXISTS service_records;
DROP TABLE IF EXISTS sop_steps;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS sop_services;
DROP TABLE IF EXISTS workstations;
DROP TABLE IF EXISTS roles;

-- Create tables

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
    is_active BOOLEAN DEFAULT '0',
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
    is_active BOOLEAN DEFAULT '0',
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
    is_normal_flow BOOLEAN DEFAULT '1',
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
    is_checked BOOLEAN DEFAULT '0',
    checked_at TIMESTAMP NULL,
    CONSTRAINT chk_checklist_id CHECK(checklist_id REGEXP '^CE[0-9]{4}$'),
    CONSTRAINT fk_service_record_id_2 FOREIGN KEY (service_record_id) REFERENCES service_records(service_record_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_step_id FOREIGN KEY (step_id) REFERENCES sop_steps(step_id) ON UPDATE CASCADE ON DELETE CASCADE
);
