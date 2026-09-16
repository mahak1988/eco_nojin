"""Generate carbon compliance modules."""
import os

BASE = "D:/eco_nojin/services/carbon/compliance"

os.makedirs(BASE, exist_ok=True)

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

with open(os.path.join(BASE, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_content)
print("init.py done")