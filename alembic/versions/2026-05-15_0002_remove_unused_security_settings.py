"""remove unused security settings

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-15 22:45:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM setting WHERE key IN ('force_https', 'secure_path')")


def downgrade() -> None:
    op.execute(
        """
        INSERT INTO setting(key, value, type, description)
        VALUES
            ('force_https', '0', 'int', '强制 HTTPS'),
            ('secure_path', '', 'str', '后台安全路径')
        ON CONFLICT (key) DO NOTHING
        """
    )
