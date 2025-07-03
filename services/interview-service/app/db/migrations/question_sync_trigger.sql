-- SQL script to create the trigger function and trigger for question sync

-- Function to notify on question changes
CREATE OR REPLACE FUNCTION notify_question_changes()
RETURNS TRIGGER AS $$
DECLARE
    data json;
    notification json;
BEGIN
    -- Build the notification object
    IF (TG_OP = 'DELETE') THEN
        data = row_to_json(OLD);
    ELSE
        data = row_to_json(NEW);
    END IF;

    -- Create notification JSON
    notification = json_build_object(
        'table', TG_TABLE_NAME,
        'action', TG_OP,
        'data', data
    );

    -- Perform notification
    -- This could be used with pg_notify or captured by a listener
    PERFORM pg_notify('question_changes', notification::text);

    -- Log the change for the message queue service to pick up
    INSERT INTO question_events (event_type, question_id, payload)
    VALUES (
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
        notification
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create the question_events table if it doesn't exist
CREATE TABLE IF NOT EXISTS question_events (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    question_id INTEGER NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on processed flag for efficient querying
CREATE INDEX IF NOT EXISTS idx_question_events_processed ON question_events(processed);

-- Add last_synced column to questions table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='questions' AND column_name='last_synced') THEN
        ALTER TABLE questions ADD COLUMN last_synced TIMESTAMP WITH TIME ZONE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='questions' AND column_name='last_updated') THEN
        ALTER TABLE questions ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- Create trigger after insert or update on questions
DROP TRIGGER IF EXISTS question_changes_trigger ON questions;
CREATE TRIGGER question_changes_trigger
AFTER INSERT OR UPDATE ON questions
FOR EACH ROW
EXECUTE FUNCTION notify_question_changes();

-- Create trigger to update last_updated timestamp
CREATE OR REPLACE FUNCTION update_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS questions_update_timestamp ON questions;
CREATE TRIGGER questions_update_timestamp
BEFORE UPDATE ON questions
FOR EACH ROW
EXECUTE FUNCTION update_last_updated();

-- Event processor function that could be called by a scheduled job
-- This function would push events to RabbitMQ
CREATE OR REPLACE FUNCTION process_question_events()
RETURNS INTEGER AS $$
DECLARE
    events_count INTEGER;
BEGIN
    -- Get count of unprocessed events
    SELECT COUNT(*) INTO events_count FROM question_events WHERE processed = FALSE;
    
    -- Here we'd typically send to RabbitMQ instead of just marking as processed
    -- For now, just mark as processed
    UPDATE question_events 
    SET processed = TRUE 
    WHERE processed = FALSE;
    
    RETURN events_count;
END;
$$ LANGUAGE plpgsql;
