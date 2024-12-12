-- Add user_id column to activities table
ALTER TABLE activities
ADD COLUMN user_id VARCHAR(36) NOT NULL,
ADD CONSTRAINT fk_activities_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Add user_id column to moments table
ALTER TABLE moments
ADD COLUMN user_id VARCHAR(36) NOT NULL,
ADD CONSTRAINT fk_moments_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Add indexes for user_id columns
CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_moments_user_id ON moments(user_id);
