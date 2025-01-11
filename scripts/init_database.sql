-- Drop and recreate database
DROP DATABASE IF EXISTS test_fridaystore;
CREATE DATABASE IF NOT EXISTS test_fridaystore
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Switch to the database
USE test_fridaystore;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    key_id VARCHAR(36) NOT NULL UNIQUE,
    user_secret VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CHECK (username != ''),
    CHECK (key_id != ''),
    CHECK (user_secret != '')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create activities table
CREATE TABLE IF NOT EXISTS activities (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    activity_schema JSON NOT NULL,
    icon VARCHAR(255) NOT NULL,
    color VARCHAR(7) NOT NULL,
    processing_status ENUM(
        'NOT_PROCESSED',
        'PENDING',
        'PROCESSING',
        'COMPLETED',
        'FAILED',
        'SKIPPED'
    ) NOT NULL DEFAULT 'NOT_PROCESSED',
    schema_render JSON NULL,
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CHECK (name != ''),
    CHECK (icon != ''),
    CHECK (color REGEXP '^#[0-9A-Fa-f]{6}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create notes table first (since it's now a leaf node)
CREATE TABLE IF NOT EXISTS notes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    attachments JSON NULL DEFAULT ('[]'),
    processing_status ENUM(
        'NOT_PROCESSED',
        'PENDING',
        'PROCESSING',
        'COMPLETED',
        'FAILED',
        'SKIPPED'
    ) NOT NULL DEFAULT 'NOT_PROCESSED',
    enrichment_data JSON NULL,
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CHECK (content != '')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create moments table
CREATE TABLE IF NOT EXISTS moments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(36) NOT NULL,
    activity_id INT NOT NULL,
    note_id INT NULL,
    data JSON NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    parent_id INT NULL,
    note_id INT NULL,
    status ENUM('TODO', 'IN_PROGRESS', 'DONE') NOT NULL DEFAULT 'TODO',
    priority ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT') NOT NULL DEFAULT 'MEDIUM',
    due_date TIMESTAMP NULL,
    tags JSON NULL DEFAULT ('[]'),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE SET NULL,
    CHECK (title != ''),
    CHECK (description != '')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add indexes for better query performance
CREATE INDEX idx_users_key_id ON users(key_id);
CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_moments_activity_id ON moments(activity_id);
CREATE INDEX idx_moments_user_id ON moments(user_id);
CREATE INDEX idx_moments_timestamp ON moments(timestamp);
CREATE INDEX idx_moments_note_id ON moments(note_id);

-- Indexes for tasks table
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_parent_id ON tasks(parent_id);
CREATE INDEX idx_tasks_note_id ON tasks(note_id);

-- Indexes for notes table
CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_created_at ON notes(created_at);
CREATE INDEX idx_notes_processing_status ON notes(processing_status);

-- Add index for processing_status (after the existing indexes)
CREATE INDEX idx_activities_processing_status ON activities(processing_status);
