"""Add feedback system tables

Revision ID: 002_add_feedback_system
Revises: 001_add_session_questions
Create Date: 2025-07-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_feedback_system'
down_revision = 'add_session_questions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create scores table
    op.create_table('scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('response_id', sa.Integer(), nullable=True),
        sa.Column('correctness', sa.Float(), nullable=False, comment='Semantic similarity to ideal answer (0-100)'),
        sa.Column('fluency', sa.Float(), nullable=False, comment='Speaking fluency score (0-100)'),
        sa.Column('depth', sa.Float(), nullable=False, comment='Answer depth and detail score (0-100)'),
        sa.Column('word_count', sa.Integer(), nullable=True, comment='Total words in response'),
        sa.Column('duration_seconds', sa.Float(), nullable=True, comment='Response duration in seconds'),
        sa.Column('words_per_minute', sa.Float(), nullable=True, comment='Speaking rate (WPM)'),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('computation_version', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['response_id'], ['responses.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scores_id'), 'scores', ['id'], unique=False)
    op.create_index(op.f('ix_scores_session_id'), 'scores', ['session_id'], unique=False)
    op.create_index(op.f('ix_scores_question_id'), 'scores', ['question_id'], unique=False)
    op.create_index(op.f('ix_scores_response_id'), 'scores', ['response_id'], unique=False)

    # Create feedback_reports table
    op.create_table('feedback_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('avg_correctness', sa.Float(), nullable=False, comment='Average correctness score (0-100)'),
        sa.Column('avg_fluency', sa.Float(), nullable=False, comment='Average fluency score (0-100)'),
        sa.Column('avg_depth', sa.Float(), nullable=False, comment='Average depth score (0-100)'),
        sa.Column('overall_score', sa.Float(), nullable=False, comment='Weighted overall score (0-100)'),
        sa.Column('correctness_percentile', sa.Float(), nullable=True, comment='Correctness percentile vs historical data'),
        sa.Column('fluency_percentile', sa.Float(), nullable=True, comment='Fluency percentile vs historical data'),
        sa.Column('depth_percentile', sa.Float(), nullable=True, comment='Depth percentile vs historical data'),
        sa.Column('overall_percentile', sa.Float(), nullable=True, comment='Overall percentile vs historical data'),
        sa.Column('report_text', sa.Text(), nullable=False, comment='AI-generated feedback narrative'),
        sa.Column('strengths', sa.JSON(), nullable=True, comment='List of identified strengths'),
        sa.Column('areas_for_improvement', sa.JSON(), nullable=True, comment='List of improvement areas'),
        sa.Column('recommendations', sa.JSON(), nullable=True, comment='Specific recommendations'),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('model_used', sa.String(length=50), nullable=True),
        sa.Column('generation_version', sa.String(length=50), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False, comment='Number of questions processed'),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True, comment='Total processing time'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_feedback_reports_id'), 'feedback_reports', ['id'], unique=False)
    op.create_index(op.f('ix_feedback_reports_session_id'), 'feedback_reports', ['session_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_feedback_reports_session_id'), table_name='feedback_reports')
    op.drop_index(op.f('ix_feedback_reports_id'), table_name='feedback_reports')
    op.drop_table('feedback_reports')
    op.drop_index(op.f('ix_scores_response_id'), table_name='scores')
    op.drop_index(op.f('ix_scores_question_id'), table_name='scores')
    op.drop_index(op.f('ix_scores_session_id'), table_name='scores')
    op.drop_index(op.f('ix_scores_id'), table_name='scores')
    op.drop_table('scores')
