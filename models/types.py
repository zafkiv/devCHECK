from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Cast:
    """Модель каста Farcaster"""
    hash: str
    author_fid: int
    author_username: str
    author_display_name: str
    text: str
    timestamp: datetime
    embeds: List[dict] = field(default_factory=list)
    mentions: List[int] = field(default_factory=list)
    likes_count: int = 0
    recasts_count: int = 0
    replies_count: int = 0
    parent_url: Optional[str] = None


@dataclass
class MonitoredFID:
    """Модель отслеживаемого FID"""
    fid: int
    username: Optional[str] = None
    last_cast_hash: Optional[str] = None
    last_checked: Optional[datetime] = None
    is_active: bool = True
    added_at: Optional[datetime] = None
    casts_sent: int = 0


@dataclass
class BotSettings:
    """Настройки бота"""
    admin_user_id: Optional[int] = None
    alert_group_id: Optional[int] = None
    is_active: bool = True
    last_updated: Optional[datetime] = None