"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('admin','reviewer','viewer', name='roleenum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_table('cases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_number', sa.String(64), nullable=False),
        sa.Column('claimant_name', sa.String(255), nullable=False),
        sa.Column('dob', sa.Date(), nullable=True),
        sa.Column('insurer', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_cases_case_number', 'cases', ['case_number'], unique=True)
    op.create_table('documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('cases.id')),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('s3_uri', sa.String(500), nullable=False),
        sa.Column('file_hash', sa.String(128), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('doc_type', sa.String(120)),
        sa.Column('excluded', sa.Boolean(), server_default='false', nullable=False),
    )
    op.create_table('pages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id')),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('ocr_text', sa.Text(), nullable=False),
        sa.Column('ocr_confidence', sa.Float(), nullable=False),
        sa.Column('text_search', postgresql.TSVECTOR()),
        sa.Column('embedding', Vector(128), nullable=True),
    )
    op.create_table('evidence',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id')),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=False),
        sa.Column('end_char', sa.Integer(), nullable=False),
        sa.Column('bbox', sa.JSON(), nullable=True),
        sa.Column('quote', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table('events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('cases.id')),
        sa.Column('event_type', sa.Enum('Encounter','Symptom','Diagnosis','Procedure','Lab','Imaging','Medication','CarePlan','Note', name='eventtypeenum')),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('start_date', sa.Date()),
        sa.Column('end_date', sa.Date()),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('structured_fields', sa.JSON(), nullable=False),
        sa.Column('verification_status', sa.Enum('unverified','verified','disputed', name='verificationenum')),
        sa.Column('evidence_ids', postgresql.ARRAY(sa.Integer())),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table('duplicate_groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('cases.id')),
        sa.Column('group_hash', sa.String(128), nullable=False),
        sa.Column('match_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table('duplicate_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('duplicate_group_id', sa.Integer(), sa.ForeignKey('duplicate_groups.id')),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id')),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('action_status', sa.Enum('None_','Keep','Remove', name='duplicateactionenum')),
    )
    op.create_table('chat_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('cases.id')),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('chat_sessions.id')),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('evidence_ids', postgresql.ARRAY(sa.Integer())),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table('report_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('section_rules', sa.JSON(), nullable=False),
    )
    op.create_table('reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('cases.id')),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('report_templates.id')),
        sa.Column('generated_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('citations_by_section', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_id', sa.Integer(), sa.ForeignKey('cases.id')),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('action_type', sa.String(120), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('reports')
    op.drop_table('report_templates')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('duplicate_items')
    op.drop_table('duplicate_groups')
    op.drop_table('events')
    op.drop_table('evidence')
    op.drop_table('pages')
    op.drop_table('documents')
    op.drop_table('cases')
    op.drop_table('users')
