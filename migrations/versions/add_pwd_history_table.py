"""Add password_history table

Revision ID: add_pwd_history
Revises: df55b6332e24
Create Date: 2026-01-18 22:55:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_pwd_history"
down_revision = "df55b6332e24"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "password_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("password_history", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_password_history_user_id"), ["user_id"], unique=False
        )


def downgrade():
    with op.batch_alter_table("password_history", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_password_history_user_id"))
    op.drop_table("password_history")
