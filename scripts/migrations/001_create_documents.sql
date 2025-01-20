-- Create documents table if it doesn't exist
CREATE TABLE IF NOT EXISTS documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    storage_url VARCHAR(1024) NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    size_bytes BIGINT NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    status ENUM('PENDING', 'ACTIVE', 'ARCHIVED', 'ERROR') NOT NULL DEFAULT 'PENDING',
    metadata JSON NULL,
    unique_name VARCHAR(128) NULL UNIQUE,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CHECK (name != ''),
    CHECK (storage_url != ''),
    CHECK (mime_type != ''),
    CHECK (size_bytes >= 0),
    CHECK (unique_name REGEXP '^[a-zA-Z0-9]+$' OR unique_name IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes for documents table
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_unique_name ON documents(unique_name);
CREATE INDEX IF NOT EXISTS idx_documents_public ON documents(is_public) WHERE is_public = TRUE;

-- Add documents relationship to users table if not exists
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS max_storage_bytes BIGINT NULL DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS used_storage_bytes BIGINT NOT NULL DEFAULT 0;

-- For existing databases, update the users table
UPDATE users
SET max_storage_bytes = 1073741824  -- 1GB default
WHERE max_storage_bytes IS NULL;
