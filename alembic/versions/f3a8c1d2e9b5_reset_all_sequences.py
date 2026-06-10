"""Reset all primary key sequences after seed data import

Revision ID: f3a8c1d2e9b5
Revises: e1082c2cfd13
Create Date: 2026-06-10
"""
from alembic import op

revision = 'f3a8c1d2e9b5'
down_revision = 'e1082c2cfd13'
branch_labels = None
depends_on = None

# (table, pk_column) pairs from the actual schema
_SEQUENCES = [
    ('department',       'department_id'),
    ('employee',         'employee_id'),
    ('saas_subscription','subscription_id'),
    ('saas_usage',       'usage_id'),
    ('transaction',      'transaction_id'),
    ('ai_payment_policy','policy_id'),
    ('approval_log',     'approval_id'),
    ('audit_log',        'audit_id'),
]


def upgrade():
    for table, col in _SEQUENCES:
        op.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', '{col}'),
                COALESCE((SELECT MAX({col}) FROM {table}), 1)
            )
        """)


def downgrade():
    pass
