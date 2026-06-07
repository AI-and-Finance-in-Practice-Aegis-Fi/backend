"""initial tables

Revision ID: bef99d9a05f3
Revises:
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa

revision = "bef99d9a05f3"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "department",
        sa.Column("department_id", sa.Integer(), primary_key=True),
        sa.Column("department_name", sa.String(100), nullable=False),
        sa.Column("monthly_budget_limit", sa.Numeric(15, 2), nullable=False),
        sa.Column("current_spending", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "employee",
        sa.Column("employee_id", sa.Integer(), primary_key=True),
        sa.Column("employee_name", sa.String(100), nullable=False),
        sa.Column("position", sa.String(100), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("department.department_id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "saas_subscription",
        sa.Column("subscription_id", sa.Integer(), primary_key=True),
        sa.Column("subscription_name", sa.String(200), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("monthly_fee", sa.Numeric(15, 2), nullable=False),
        sa.Column("total_seats", sa.Integer(), nullable=False),
        sa.Column("used_seats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wasted_amount", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.Enum("LOW", "MEDIUM", "HIGH", name="risk_level_enum"), nullable=False, server_default="LOW"),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("department.department_id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "saas_usage",
        sa.Column("usage_id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee.employee_id"), nullable=False),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("saas_subscription.subscription_id"), nullable=False),
        sa.Column("last_login_date", sa.Date(), nullable=True),
        sa.Column("monthly_usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_ghost_account", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "transaction",
        sa.Column("transaction_id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee.employee_id"), nullable=False),
        sa.Column("merchant_name", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("user_input_reason", sa.String(500), nullable=True),
        sa.Column("ai_predicted_reason", sa.String(500), nullable=True),
        sa.Column("is_approved", sa.Boolean(), nullable=True),
        sa.Column("ai_risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("ai_risk_reason", sa.Text(), nullable=True),
        sa.Column("payment_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "ai_payment_policy",
        sa.Column("policy_id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee.employee_id"), nullable=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("department.department_id"), nullable=True),
        sa.Column("restricted_category", sa.String(100), nullable=True),
        sa.Column("single_payment_limit", sa.Numeric(15, 2), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "approval_log",
        sa.Column("approval_id", sa.Integer(), primary_key=True),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transaction.transaction_id"), nullable=False),
        sa.Column("approver_employee_id", sa.Integer(), sa.ForeignKey("employee.employee_id"), nullable=False),
        sa.Column("approval_result", sa.Boolean(), nullable=False),
        sa.Column("approval_reason", sa.String(500), nullable=True),
        sa.Column("approval_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("approval_log")
    op.drop_table("ai_payment_policy")
    op.drop_table("transaction")
    op.drop_table("saas_usage")
    op.drop_table("saas_subscription")
    op.drop_table("employee")
    op.drop_table("department")
    op.execute("DROP TYPE IF EXISTS risk_level_enum")
