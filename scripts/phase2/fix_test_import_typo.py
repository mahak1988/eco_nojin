#!/usr/bin/env python3
"""Fix typo in test import: mock_generator → mockGenerator"""

import structlog

logger = structlog.get_logger()
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_FILE = PROJECT_ROOT / "frontend" / "src" / "features" / "crypto-payment" / "__tests__" / "mockGenerator.test.ts"

if TEST_FILE.exists():
    text = TEST_FILE.read_text(encoding="utf-8")
    fixed = text.replace(
        "from '../utils/mock_generator'",
        "from '../utils/mockGenerator'"
    )
    TEST_FILE.write_text(fixed, encoding="utf-8")
    logger.info(f"✓ اصلاح شد: {TEST_FILE.name}")
else:
    logger.info(f"✗ فایل یافت نشد")
