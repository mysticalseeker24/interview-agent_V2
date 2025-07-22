-- TalentSync Interview Service - Supabase Migration
-- This script creates the necessary tables for session management in Supabase

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create interview_sessions table
CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    module_id VARCHAR(255) NOT NULL,
    mode VARCHAR(50) NOT NULL DEFAULT 'practice',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    current_question_index INTEGER NOT NULL DEFAULT 0,
    estimated_duration_minutes INTEGER NOT NULL DEFAULT 30,
    queue_length INTEGER NOT NULL DEFAULT 0,
    asked_questions JSONB DEFAULT '[]'::jsonb,
    parsed_resume_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create session_queues table for question queue management
CREATE TABLE IF NOT EXISTS session_queues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question_id VARCHAR(255) NOT NULL,
    sequence_index INTEGER NOT NULL,
    question_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, question_id)
);

-- Create session_answers table for tracking answers
CREATE TABLE IF NOT EXISTS session_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question_id VARCHAR(255) NOT NULL,
    answer_text TEXT NOT NULL,
    audio_file_path VARCHAR(500),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds FLOAT,
    confidence_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_id ON interview_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_created_at ON interview_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_session_queues_session_id ON session_queues(session_id);
CREATE INDEX IF NOT EXISTS idx_session_answers_session_id ON session_answers(session_id);

-- Enable Row Level Security (RLS)
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_queues ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_answers ENABLE ROW LEVEL SECURITY;

-- RLS Policies for interview_sessions
CREATE POLICY "Users can view own sessions" ON interview_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own sessions" ON interview_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON interview_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions" ON interview_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for session_queues
CREATE POLICY "Users can view own session queues" ON session_queues
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM interview_sessions 
            WHERE interview_sessions.id = session_queues.session_id 
            AND interview_sessions.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage own session queues" ON session_queues
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM interview_sessions 
            WHERE interview_sessions.id = session_queues.session_id 
            AND interview_sessions.user_id = auth.uid()
        )
    );

-- RLS Policies for session_answers
CREATE POLICY "Users can view own session answers" ON session_answers
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM interview_sessions 
            WHERE interview_sessions.id = session_answers.session_id 
            AND interview_sessions.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage own session answers" ON session_answers
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM interview_sessions 
            WHERE interview_sessions.id = session_answers.session_id 
            AND interview_sessions.user_id = auth.uid()
        )
    );

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_interview_sessions_updated_at 
    BEFORE UPDATE ON interview_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean up expired sessions (older than 24 hours)
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM interview_sessions 
    WHERE created_at < NOW() - INTERVAL '24 hours' 
    AND status IN ('pending', 'cancelled');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to clean up expired sessions (if using pg_cron extension)
-- Note: This requires the pg_cron extension to be enabled
-- SELECT cron.schedule('cleanup-expired-sessions', '0 */6 * * *', 'SELECT cleanup_expired_sessions();');

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated; 