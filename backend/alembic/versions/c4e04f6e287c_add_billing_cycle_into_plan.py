"""add billing cycle into plan

Revision ID: c4e04f6e287c
Revises: 8773c258e1ff
Create Date: 2025-11-10 12:02:19.604157

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4e04f6e287c'
down_revision: str | Sequence[str] | None = '8773c258e1ff'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Định nghĩa ENUM type
billing_cycle_enum = sa.Enum(
    'MONTHLY', 'YEARLY', 'LIFETIME',
    name='billing_cycle'
)

def upgrade() -> None:
    """Upgrade schema."""
    # ### Đã sửa code ###

    # 1. Tạo ENUM type trong PostgreSQL trước
    billing_cycle_enum.create(op.get_bind())

    # 2. Sử dụng op.add_column để THÊM cột mới
    op.add_column(
        'plans',
        sa.Column(
            'billing_cycle',
            billing_cycle_enum,         # Dùng type ENUM đã định nghĩa
            nullable=False,             # Đặt là NOT NULL
            server_default='MONTHLY'  # Thêm giá trị default cho các hàng đã có
        )
    )
    # ### kết thúc sửa code ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### Đã sửa code ###

    # 1. Xóa cột 'billing_cycle' khỏi bảng 'plans'
    op.drop_column('plans', 'billing_cycle')

    # 2. Sau khi cột đã bị xóa, xóa ENUM type
    billing_cycle_enum.drop(op.get_bind())

    # ### kết thúc sửa code ###
