CREATE TABLE equipment (
    equipment_id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_name VARCHAR(100) NOT NULL,
    serial_number VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(100) NOT NULL,
    purchase_date DATE,
    status ENUM(
        'Active',
        'Under Maintenance',
        'Decommissioned'
    ) DEFAULT 'Active'
);

CREATE TABLE maintenance_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_id INT NOT NULL,
    maintenance_date DATE NOT NULL,
    technician_name VARCHAR(100) NOT NULL,
    issue_reported TEXT,
    resolution_notes TEXT,
    next_due_date DATE,
    FOREIGN KEY (equipment_id)
        REFERENCES equipment(equipment_id)
        ON DELETE CASCADE
);