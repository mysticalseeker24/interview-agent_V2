"""Add session_questions table for tracking asked questions

Revision ID: add_session_questions
Revises: 
Create Date: 2025-07-04 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_session_questions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create session_questions table."""
    op.create_table(
        'session_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('asked_at', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_session_questions_id'), 'session_questions', ['id'], unique=False)
    op.create_index(op.f('ix_session_questions_session_id'), 'session_questions', ['session_id'], unique=False)


def downgrade():
    """Drop session_questions table."""
    op.drop_index(op.f('ix_session_questions_session_id'), table_name='session_questions')
    op.drop_index(op.f('ix_session_questions_id'), table_name='session_questions')
    op.drop_table('session_questions')
