import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE = Path("D:/eco_nojin/services/carbon/compliance")

BASE.mkdir(parents=True, exist_ok=True)

# __init__.py
init_content = '''"""Carbon credit compliance module.

Provides KYC/AML, greenwashing prevention, and regulatory safeguards for
carbon credit issuance and tokenization.
"""

from services.carbon.compliance.kyc_aml import (
    AMLCheck,
    KYCRecord,
    KYCService,
    RiskLevel,
)
from services.carbon.compliance.greenwashing_guard import (
    GreenwashingGuard,
    DisclosureRecord,
)

__all__ = [
    "AMLCheck",
    "DisclosureRecord",
    "GreenwashingGuard",
    "KYCRecord",
    "KYCService",
    "RiskLevel",
]
'''

(BASE / "__init__.py").write_text(init_content, encoding="utf-8")
logger.info("init.py done")
