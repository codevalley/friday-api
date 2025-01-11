-- Add schema render columns to activities table
ALTER TABLE activities
ADD COLUMN processing_status ENUM(
    'NOT_PROCESSED',
    'PENDING',
    'PROCESSING',
    'COMPLETED',
    'FAILED',
    'SKIPPED'
) NOT NULL DEFAULT 'NOT_PROCESSED',
ADD COLUMN schema_render JSON NULL,
ADD COLUMN processed_at TIMESTAMP NULL;

-- Add index for processing_status
CREATE INDEX idx_activities_processing_status ON activities(processing_status);
