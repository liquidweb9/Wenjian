-- Add job_target_id column to interviews table
-- Migration: add_job_target_to_interviews
-- Date: 2026-08-04

ALTER TABLE interviews
ADD COLUMN job_target_id VARCHAR(64) NULL,
ADD CONSTRAINT fk_interviews_job_target
    FOREIGN KEY (job_target_id)
    REFERENCES job_targets(job_target_id)
    ON DELETE SET NULL;

-- Create index for faster lookups
CREATE INDEX idx_interviews_job_target_id ON interviews(job_target_id);

-- Comment on the column
COMMENT ON COLUMN interviews.job_target_id IS 'Optional reference to a job target for gap-driven interview planning';
