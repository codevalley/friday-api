    -- Create the database if it doesn't exist
    CREATE DATABASE IF NOT EXISTS test_fridaystore;

    -- Switch to the database
    USE test_fridaystore;

    -- Create users table
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(36) PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        key_id VARCHAR(36) NOT NULL UNIQUE,
        user_secret VARCHAR(64) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );

    -- Create activities table
    CREATE TABLE IF NOT EXISTS activities (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_id VARCHAR(36) NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        activity_schema JSON NOT NULL,
        icon VARCHAR(255) NOT NULL,
        color VARCHAR(7) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- Create moments table
    CREATE TABLE IF NOT EXISTS moments (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_id VARCHAR(36) NOT NULL,
        activity_id INT NOT NULL,
        data JSON NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- Add indexes
    CREATE INDEX idx_users_key_id ON users(key_id);
    CREATE INDEX idx_activities_user_id ON activities(user_id);
    CREATE INDEX idx_moments_activity_id ON moments(activity_id);
    CREATE INDEX idx_moments_user_id ON moments(user_id);
    CREATE INDEX idx_moments_timestamp ON moments(timestamp);
