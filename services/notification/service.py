"""
سرویس اعلان‌ها (Notification Service)
نسخه استاندارد برای پذیرش db/session
"""

from typing import Optional

class NotificationService:
    """سرویس اعلان‌ها"""

    def __init__(self, db=None, session=None):
        self.db = db
        self.session = session

    def health(self):
        return "ok"
