-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS test_fridaystore;

-- Switch to the database
USE test_fridaystore;

-- Create activities table
CREATE TABLE IF NOT EXISTS activities (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    activity_schema JSON NOT NULL,
    icon VARCHAR(255) NOT NULL,
    color VARCHAR(7) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create moments table
CREATE TABLE IF NOT EXISTS moments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    activity_id INT NOT NULL,
    data JSON NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Add indexes
CREATE INDEX idx_moments_activity_id ON moments(activity_id);
CREATE INDEX idx_moments_timestamp ON moments(timestamp);
