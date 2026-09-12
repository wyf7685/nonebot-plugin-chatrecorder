"""add_message_query_index

Migration ID: cd638a093be9
Parent migration: bc43ce947963
Created: 2026-09-12

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "cd638a093be9"
down_revision: str | Sequence[str] | None = "bc43ce947963"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE_NAME = "nonebot_plugin_chatrecorder_messagerecord_v2"
_INDEX_NAME = "ix_chatrecorder_message_session_time_id"


def upgrade(name: str = "") -> None:
    if name:
        return
    op.create_index(
        _INDEX_NAME,
        _TABLE_NAME,
        ["session_persist_id", "time", "id"],
        unique=False,
    )


def downgrade(name: str = "") -> None:
    if name:
        return
    op.drop_index(_INDEX_NAME, table_name=_TABLE_NAME)
