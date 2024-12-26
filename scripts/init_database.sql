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
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CHECK (name != ''),
    CHECK (icon != ''),
    CHECK (color REGEXP '^#[0-9A-Fa-f]{6}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create moments table
CREATE TABLE IF NOT EXISTS moments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(36) NOT NULL,
    activity_id INT NOT NULL,
    data JSON NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create notes table
-- This table stores user notes with optional attachments (voice, photo, or file)
CREATE TABLE IF NOT EXISTS notes (
    -- Primary key and relationships
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(36) NOT NULL,

    -- Note content
    content TEXT NOT NULL,

    -- New columns needed for activity/moment references
    activity_id INT NULL,
    moment_id INT NULL,

    -- Changed attachment columns
    attachment_url VARCHAR(500) NULL,
    attachment_type ENUM('IMAGE', 'DOCUMENT', 'LINK') NULL,  -- Updated enum values
    attachments JSON NULL,  -- New column for structured attachments

    -- Processing status
    processing_status ENUM(
        'not_processed',
        'pending',
        'processing',
        'completed',
        'failed',
        'skipped'
    ) NOT NULL DEFAULT 'not_processed',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign keys and constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (activity_id) REFERENCES activities(id),  -- New FK
    FOREIGN KEY (moment_id) REFERENCES moments(id),  -- New FK

    -- Data validation
    CONSTRAINT check_content_not_empty CHECK (content != ''),
    CONSTRAINT check_attachment_consistency
        CHECK ((attachment_url IS NULL AND attachment_type IS NULL) OR
               (attachment_url IS NOT NULL AND attachment_type IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add indexes for better query performance
CREATE INDEX idx_users_key_id ON users(key_id);
CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_moments_activity_id ON moments(activity_id);
CREATE INDEX idx_moments_user_id ON moments(user_id);
CREATE INDEX idx_moments_timestamp ON moments(timestamp);

-- Indexes for notes table
CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_created_at ON notes(created_at);
CREATE INDEX idx_notes_attachment_type ON notes(attachment_type);
