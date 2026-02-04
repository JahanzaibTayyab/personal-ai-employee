"""Watcher modules for file system and Gmail monitoring."""

from ai_employee.watchers.approval import ApprovalWatcher
from ai_employee.watchers.base import BaseWatcher
from ai_employee.watchers.whatsapp import (
    WhatsAppWatcher,
    WhatsAppWatcherStatus,
    parse_whatsapp_message,
)

__all__ = [
    "ApprovalWatcher",
    "BaseWatcher",
    "WhatsAppWatcher",
    "WhatsAppWatcherStatus",
    "parse_whatsapp_message",
]
