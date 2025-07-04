"""Add question sync columns migration

Revision ID: 20250703001
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '20250703001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add last_synced and domain columns to questions table
    op.add_column('questions', sa.Column('last_synced', sa.DateTime(), nullable=True))
    op.add_column('questions', sa.Column('domain', sa.String(100), nullable=True, server_default='general'))
    
    # Create trigger function for question changes
    op.execute("""
    CREATE OR REPLACE FUNCTION update_question_timestamp()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger
    op.execute("""
    DROP TRIGGER IF EXISTS update_question_timestamp ON questions;
    CREATE TRIGGER update_question_timestamp
    BEFORE UPDATE ON questions
    FOR EACH ROW
    EXECUTE FUNCTION update_question_timestamp();
    """)

def downgrade():
    # Drop the trigger
    op.execute("DROP TRIGGER IF EXISTS update_question_timestamp ON questions;")
    op.execute("DROP FUNCTION IF EXISTS update_question_timestamp();")
    
    # Drop the columns
    op.drop_column('questions', 'domain')
    op.drop_column('questions', 'last_synced')
