"""سرویس LedgerService (Placeholder برای production)"""


class LedgerService:
    """کلاس سرویس ledger"""

    def __init__(self, db=None, session=None):
        self.db = db
        self.session = session

    def health(self):
        return "ok"

    # متدهای اصلی به‌مرور اضافه می‌شوند
