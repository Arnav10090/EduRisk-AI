"""Initial schema with students, predictions, and audit_logs tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create students table
    op.create_table(
        'students',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Student full name'),
        sa.Column('course_type', sa.String(length=100), nullable=False, comment='Course type (e.g., Engineering, MBA, etc.)'),
        sa.Column('institute_name', sa.String(length=255), nullable=True, comment='Name of the educational institute'),
        sa.Column('institute_tier', sa.Integer(), nullable=False, comment='Institute tier classification (1-3, where 1 is highest)'),
        sa.Column('cgpa', sa.Numeric(precision=4, scale=2), nullable=True, comment='Cumulative Grade Point Average'),
        sa.Column('cgpa_scale', sa.Numeric(precision=4, scale=2), server_default='10.0', nullable=False, comment='CGPA scale (typically 4.0 or 10.0)'),
        sa.Column('year_of_grad', sa.Integer(), nullable=False, comment='Year of graduation'),
        sa.Column('internship_count', sa.Integer(), server_default='0', nullable=False, comment='Number of internships completed'),
        sa.Column('internship_months', sa.Integer(), server_default='0', nullable=False, comment='Total months of internship experience'),
        sa.Column('internship_employer_type', sa.String(length=100), nullable=True, comment='Type of internship employer (MNC, Startup, PSU, NGO, etc.)'),
        sa.Column('certifications', sa.Integer(), server_default='0', nullable=False, comment='Number of professional certifications'),
        sa.Column('region', sa.String(length=100), nullable=True, comment='Geographic region (North, South, East, West, etc.)'),
        sa.Column('loan_amount', sa.Numeric(precision=12, scale=2), nullable=True, comment='Total loan amount in INR'),
        sa.Column('loan_emi', sa.Numeric(precision=10, scale=2), nullable=True, comment='Monthly EMI amount in INR'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.CheckConstraint('institute_tier >= 1 AND institute_tier <= 3', name='check_institute_tier_range'),
        sa.CheckConstraint('cgpa >= 0', name='check_cgpa_non_negative'),
        sa.CheckConstraint('cgpa <= cgpa_scale', name='check_cgpa_within_scale'),
        sa.CheckConstraint('year_of_grad >= 2020 AND year_of_grad <= 2030', name='check_year_of_grad_range'),
        sa.CheckConstraint('internship_count >= 0', name='check_internship_count_non_negative'),
        sa.CheckConstraint('internship_months >= 0', name='check_internship_months_non_negative'),
        sa.CheckConstraint('certifications >= 0', name='check_certifications_non_negative'),
        sa.CheckConstraint('loan_amount >= 0', name='check_loan_amount_non_negative'),
        sa.CheckConstraint('loan_emi >= 0', name='check_loan_emi_non_negative'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for students table
    op.create_index('idx_students_tier', 'students', ['institute_tier'])
    op.create_index('idx_students_course', 'students', ['course_type'])
    op.create_index('idx_students_created', 'students', [sa.text('created_at DESC')])
    
    # Create predictions table
    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Reference to student record'),
        sa.Column('model_version', sa.String(length=50), nullable=False, comment='ML model version used for prediction'),
        sa.Column('prob_placed_3m', sa.Numeric(precision=5, scale=4), nullable=False, comment='Probability of placement within 3 months (0.0000-1.0000)'),
        sa.Column('prob_placed_6m', sa.Numeric(precision=5, scale=4), nullable=False, comment='Probability of placement within 6 months (0.0000-1.0000)'),
        sa.Column('prob_placed_12m', sa.Numeric(precision=5, scale=4), nullable=False, comment='Probability of placement within 12 months (0.0000-1.0000)'),
        sa.Column('placement_label', sa.String(length=50), nullable=False, comment='Placement timeline label (placed_3m, placed_6m, placed_12m, high_risk)'),
        sa.Column('risk_score', sa.Integer(), nullable=False, comment='Composite risk score (0-100, higher = more risk)'),
        sa.Column('risk_level', sa.String(length=20), nullable=False, comment='Risk level category (low, medium, high)'),
        sa.Column('salary_min', sa.Numeric(precision=10, scale=2), nullable=True, comment='Minimum predicted salary in LPA (Lakhs Per Annum)'),
        sa.Column('salary_max', sa.Numeric(precision=10, scale=2), nullable=True, comment='Maximum predicted salary in LPA'),
        sa.Column('salary_confidence', sa.Numeric(precision=4, scale=2), nullable=True, comment='Salary prediction confidence percentage'),
        sa.Column('emi_affordability', sa.Numeric(precision=5, scale=2), nullable=True, comment='Ratio of loan EMI to predicted monthly salary'),
        sa.Column('shap_values', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Complete SHAP feature attribution values as JSON'),
        sa.Column('top_risk_drivers', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Top 5 risk drivers with feature, value, and direction'),
        sa.Column('ai_summary', sa.Text(), nullable=True, comment='Natural language risk summary generated by LLM'),
        sa.Column('next_best_actions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Recommended interventions as JSON array'),
        sa.Column('alert_triggered', sa.Boolean(), server_default='false', nullable=False, comment='Whether high-risk alert was triggered'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Prediction creation timestamp'),
        sa.CheckConstraint('prob_placed_3m >= 0 AND prob_placed_3m <= 1', name='check_prob_3m_range'),
        sa.CheckConstraint('prob_placed_6m >= 0 AND prob_placed_6m <= 1', name='check_prob_6m_range'),
        sa.CheckConstraint('prob_placed_12m >= 0 AND prob_placed_12m <= 1', name='check_prob_12m_range'),
        sa.CheckConstraint('risk_score >= 0 AND risk_score <= 100', name='check_risk_score_range'),
        sa.CheckConstraint("risk_level IN ('low', 'medium', 'high')", name='check_risk_level_enum'),
        sa.CheckConstraint("placement_label IN ('placed_3m', 'placed_6m', 'placed_12m', 'high_risk')", name='check_placement_label_enum'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for predictions table
    op.create_index('idx_predictions_student', 'predictions', ['student_id'])
    op.create_index('idx_predictions_risk_level', 'predictions', ['risk_level'])
    op.create_index('idx_predictions_risk_score', 'predictions', ['risk_score'])
    op.create_index('idx_predictions_created', 'predictions', [sa.text('created_at DESC')])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Reference to student record (nullable for audit preservation)'),
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Reference to prediction record (nullable for audit preservation)'),
        sa.Column('action', sa.String(length=100), nullable=False, comment='Action type (PREDICT, EXPLAIN, ALERT_SENT, etc.)'),
        sa.Column('performed_by', sa.String(length=100), nullable=True, comment='User or system identifier that performed the action'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional action metadata (model_version, processing_time, etc.)'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Action timestamp'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit_logs table
    op.create_index('idx_audit_logs_student', 'audit_logs', ['student_id'])
    op.create_index('idx_audit_logs_prediction', 'audit_logs', ['prediction_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_created', 'audit_logs', [sa.text('created_at DESC')])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('audit_logs')
    op.drop_table('predictions')
    op.drop_table('students')
