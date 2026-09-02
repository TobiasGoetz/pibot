"""User activity record schema."""

from collections.abc import Mapping
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserStatsRecord(BaseModel):
    """Per-member activity stats for one guild."""

    model_config = ConfigDict(frozen=True)

    guildId: int
    userId: int
    messageCount: int = 0
    lastMessageAt: datetime | None = None
    firstSeenAt: datetime | None = None

    @classmethod
    def fromDocument(cls, doc: Mapping[str, object] | None) -> UserStatsRecord | None:
        """Build a record from a MongoDB document."""
        if doc is None:
            return None
        docId = doc.get("_id")
        if not isinstance(docId, Mapping):
            return None
        return cls.model_validate(
            {
                "guildId": docId.get("guildId"),
                "userId": docId.get("userId"),
                "messageCount": doc.get("messageCount", 0),
                "lastMessageAt": doc.get("lastMessageAt"),
                "firstSeenAt": doc.get("firstSeenAt"),
            }
        )
