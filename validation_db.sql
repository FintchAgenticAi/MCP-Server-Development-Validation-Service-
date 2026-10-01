-- =============================================================================
-- DATABASE IMPLEMENTATION: VALIDATION SERVICE (SILVER ZONE)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS validation_db;
USE validation_db;

-- -----------------------------------------------------------------------------
-- 1. TABLE: validation_categories
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    CONSTRAINT uk_category_name UNIQUE (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 2. TABLE: validation_rules
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_code VARCHAR(50) NOT NULL,
    rule_name VARCHAR(150) NOT NULL,
    description VARCHAR(500),
    severity_level ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'MEDIUM',
    category_id INT NOT NULL,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    is_system_rule ENUM('Y', 'N') NOT NULL DEFAULT 'N',
    created_by VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uk_rule_code UNIQUE (rule_code),
    CONSTRAINT fk_rules_category FOREIGN KEY (category_id) 
        REFERENCES validation_categories(category_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 3. TABLE: validation_rule_versions
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_rule_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    version_no VARCHAR(20) NOT NULL,
    effective_from DATETIME NOT NULL,
    effective_to DATETIME DEFAULT NULL,
    status ENUM('draft', 'active', 'retired') NOT NULL DEFAULT 'draft',
    change_log TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_versions_rule FOREIGN KEY (rule_id) 
        REFERENCES validation_rules(rule_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 4. TABLE: validation_rule_methods
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_rule_methods (
    method_id INT AUTO_INCREMENT PRIMARY KEY,
    version_id INT NOT NULL,
    method_name VARCHAR(150) NOT NULL,
    method_path VARCHAR(255) NOT NULL,
    entry_point VARCHAR(100) NOT NULL DEFAULT 'apply',
    description VARCHAR(255),
    CONSTRAINT fk_methods_version FOREIGN KEY (version_id) 
        REFERENCES validation_rule_versions(version_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 5. TABLE: validation_rule_parameters
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_rule_parameters (
    param_id INT AUTO_INCREMENT PRIMARY KEY,
    method_id INT NOT NULL,
    param_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    is_required ENUM('Y', 'N') NOT NULL DEFAULT 'Y',
    default_value VARCHAR(255) DEFAULT NULL,
    description VARCHAR(255),
    CONSTRAINT fk_params_method FOREIGN KEY (method_id) 
        REFERENCES validation_rule_methods(method_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 6. TABLE: validation_rule_dependencies
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_rule_dependencies (
    dependency_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    depends_on_rule_id INT NOT NULL,
    dependency_type ENUM('hard', 'soft') NOT NULL DEFAULT 'hard',
    description VARCHAR(255),
    CONSTRAINT fk_dep_rule FOREIGN KEY (rule_id) 
        REFERENCES validation_rules(rule_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_dep_depends_on FOREIGN KEY (depends_on_rule_id) 
        REFERENCES validation_rules(rule_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 7. TABLE: validation_rule_tags & MAP
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_rule_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    CONSTRAINT uk_tag_name UNIQUE (tag_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS validation_rule_tag_map (
    rule_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (rule_id, tag_id),
    CONSTRAINT fk_tagmap_rule FOREIGN KEY (rule_id) 
        REFERENCES validation_rules(rule_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tagmap_tag FOREIGN KEY (tag_id) 
        REFERENCES validation_rule_tags(tag_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 8. TABLE: validation_rule_usages
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_rule_usages (
    usage_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    used_in_service VARCHAR(100) NOT NULL,
    used_in_method VARCHAR(150) NOT NULL,
    description VARCHAR(255),
    CONSTRAINT fk_usages_rule FOREIGN KEY (rule_id) 
        REFERENCES validation_rules(rule_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 9. TABLE: validation_logic_logs
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_logic_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    method_id INT NOT NULL,
    version_id INT NOT NULL,
    request_id VARCHAR(100) NOT NULL,
    input_record_count INT NOT NULL DEFAULT 0,
    passed_record_count INT NOT NULL DEFAULT 0,
    failed_record_count INT NOT NULL DEFAULT 0,
    quarantine_status ENUM('passed', 'quarantined', 'discarded') NOT NULL,
    status ENUM('success', 'failed', 'partial') NOT NULL,
    started_at DATETIME NOT NULL,
    ended_at DATETIME DEFAULT NULL,
    error_message TEXT DEFAULT NULL,
    triggered_by ENUM('manual', 'api', 'system') NOT NULL DEFAULT 'system',
    CONSTRAINT fk_logs_rule FOREIGN KEY (rule_id) 
        REFERENCES validation_rules(rule_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_logs_method FOREIGN KEY (method_id) 
        REFERENCES validation_rule_methods(method_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_logs_version FOREIGN KEY (version_id) 
        REFERENCES validation_rule_versions(version_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- PERFORMANCE INDEXES
-- -----------------------------------------------------------------------------
CREATE INDEX idx_rules_status ON validation_rules(status);
CREATE INDEX idx_logs_request_id ON validation_logic_logs(request_id);
CREATE INDEX idx_logs_quarantine ON validation_logic_logs(quarantine_status);