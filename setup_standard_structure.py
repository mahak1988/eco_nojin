#!/usr/bin/env python3
"""
Eco Nojin - Standard Structure Setup
=====================================
1. Marks natural placeholders (__init__.py) as NORMAL
2. Creates standard structure for all modules
3. Generates module templates

Usage:
  python setup_standard_structure.py [--dry-run] [--create-templates]
"""
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


PROJECT_ROOT = Path(__file__).parent
REPORT_FILE = PROJECT_ROOT / "structure_setup_report.json"
REPORT_MD = PROJECT_ROOT / "structure_setup_report.md"

# Standard module structure
STANDARD_STRUCTURE = {
    '__init__.py': '''"""
{module_name} module for Eco Nojin.

{module_description}

Author: Eco Nojin Team
Created: {date}
"""

__version__ = "0.1.0"
__author__ = "Eco Nojin Team"

# Module exports
__all__ = []
''',
    
    'models.py': '''"""
Data models for {module_name} module.

This module contains Pydantic models and dataclasses
for {module_description}
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Base{module_class}(BaseModel):
    """Base model for {module_name}."""
    
    id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class {module_class}Create(BaseModel):
    """Model for creating {module_name}."""
    pass


class {module_class}Read(BaseModel):
    """Model for reading {module_name}."""
    pass


class {module_class}Update(BaseModel):
    """Model for updating {module_name}."""
    pass
''',
    
    'core.py': '''"""
Core business logic for {module_name} module.

{module_description}
"""
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class {module_class}Service:
    """Main service class for {module_name} operations."""
    
    def __init__(self):
        """Initialize the service."""
        logger.info("Initializing {module_name} service")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Dict: Processed results
            
        Raises:
            ValueError: If input data is invalid
        """
        # Validate input
        if not data:
            raise ValueError("Input data cannot be empty")
        
        # Process data
        result = {
            'status': 'success',
            'data': data,
            'processed_at': datetime.utcnow().isoformat()
        }
        
        logger.info("Data processed successfully")
        return result
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data.
        
        Args:
            data: Input data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not data:
            return False
        
        # Add validation logic here
        return True
''',
    
    'utils.py': '''"""
Utility functions for {module_name} module.
"""
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def validate_range(value: float, min_val: float, max_val: float, name: str) -> None:
    """Validate that a value is within range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the parameter (for error messages)
        
    Raises:
        ValueError: If value is out of range
    """
    if value < min_val or value > max_val:
        raise ValueError(f"{name} must be between {min_val} and {max_val}")


def normalize_percentage(value: float) -> float:
    """Normalize a percentage value to 0-100 range.
    
    Args:
        value: Percentage value
        
    Returns:
        float: Normalized percentage
        
    Raises:
        ValueError: If value is negative
    """
    if value < 0:
        raise ValueError("Percentage cannot be negative")
    return min(100.0, value)


def format_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format result for API response.
    
    Args:
        data: Raw result data
        
    Returns:
        Dict: Formatted result
    """
    return {
        'status': 'success',
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }
''',
    
    'api.py': '''"""
API endpoints for {module_name} module.
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .core import {module_class}Service
from .models import {module_class}Create, {module_class}Read, {module_class}Update

router = APIRouter(prefix="/{module_name}", tags=["{module_name}"])

# Service instance
_service = {module_class}Service()


class {module_class}Request(BaseModel):
    """Request model for {module_name}."""
    pass


class {module_class}Response(BaseModel):
    """Response model for {module_name}."""
    status: str
    data: Dict
    message: Optional[str] = None


@router.post("/analyze", response_model={module_class}Response)
async def analyze(request: {module_class}Request):
    """Analyze {module_name} data.
    
    Args:
        request: Analysis request
        
    Returns:
        Analysis results
    """
    try:
        result = _service.process(request.dict())
        return {module_class}Response(status="success", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "module": "{module_name}"}
''',
    
    'tests/__init__.py': '''"""Tests for {module_name} module."""
''',
    
    'tests/test_{module_name}.py': '''"""
Unit tests for {module_name} module.
"""
import pytest
from {module_path} import {module_class}Service


class Test{module_class}Service:
    """Tests for {module_class}Service."""
    
    @pytest.fixture
    def service(self):
        """Create service instance."""
        return {module_class}Service()
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service is not None
    
    def test_process_valid_data(self, service):
        """Test processing valid data."""
        data = {{"key": "value"}}
        result = service.process(data)
        assert result["status"] == "success"
    
    def test_process_empty_data(self, service):
        """Test processing empty data raises error."""
        with pytest.raises(ValueError):
            service.process({{}})
    
    def test_validate_input_valid(self, service):
        """Test input validation with valid data."""
        data = {{"key": "value"}}
        assert service.validate_input(data) is True
    
    def test_validate_input_empty(self, service):
        """Test input validation with empty data."""
        assert service.validate_input({{}}) is False


class TestUtils:
    """Tests for utility functions."""
    
    def test_validate_range_valid(self):
        """Test range validation with valid value."""
        from {module_path}.utils import validate_range
        validate_range(50, 0, 100, "test")  # Should not raise
    
    def test_validate_range_invalid(self):
        """Test range validation with invalid value."""
        from {module_path}.utils import validate_range
        with pytest.raises(ValueError):
            validate_range(150, 0, 100, "test")
    
    def test_normalize_percentage_valid(self):
        """Test percentage normalization."""
        from {module_path}.utils import normalize_percentage
        assert normalize_percentage(50) == 50
        assert normalize_percentage(150) == 100
    
    def test_normalize_percentage_negative(self):
        """Test percentage normalization with negative value."""
        from {module_path}.utils import normalize_percentage
        with pytest.raises(ValueError):
            normalize_percentage(-10)
'''
}

# Module definitions with descriptions
MODULES = {
    # Engine modules
    'engine/hydroma/soil': {
        'name': 'soil',
        'class': 'Soil',
        'description': 'Soil analysis, classification, and health assessment',
        'priority': 'P1'
    },
    'engine/hydroma/hydrology': {
        'name': 'hydrology',
        'class': 'Hydrology',
        'description': 'Hydrological calculations and water balance modeling',
        'priority': 'P1'
    },
    'engine/hydroma/crop': {
        'name': 'crop',
        'class': 'Crop',
        'description': 'Crop growth modeling and yield prediction',
        'priority': 'P1'
    },
    'engine/hydroma/geospatial': {
        'name': 'geospatial',
        'class': 'Geospatial',
        'description': 'Geospatial analysis and mapping utilities',
        'priority': 'P1'
    },
    'engine/hydroma/mrv': {
        'name': 'mrv',
        'class': 'MRV',
        'description': 'Measurement, Reporting, and Verification for carbon credits',
        'priority': 'P2'
    },
    'engine/hydroma/erosion': {
        'name': 'erosion',
        'class': 'Erosion',
        'description': 'Soil erosion modeling and risk assessment',
        'priority': 'P2'
    },
    'engine/hydroma/groundwater': {
        'name': 'groundwater',
        'class': 'Groundwater',
        'description': 'Groundwater modeling and aquifer analysis',
        'priority': 'P2'
    },
    'engine/hydroma/finance': {
        'name': 'finance',
        'class': 'Finance',
        'description': 'Financial analysis and economic modeling',
        'priority': 'P3'
    },
    'engine/hydroma/plants': {
        'name': 'plants',
        'class': 'Plants',
        'description': 'Plant database and species information',
        'priority': 'P3'
    },
    'engine/hydroma/risk': {
        'name': 'risk',
        'class': 'Risk',
        'description': 'Risk assessment and management',
        'priority': 'P3'
    },
    'engine/hydroma/ml': {
        'name': 'ml',
        'class': 'ML',
        'description': 'Machine learning models for prediction',
        'priority': 'P3'
    },
    'engine/hydroma/ecotourism': {
        'name': 'ecotourism',
        'class': 'Ecotourism',
        'description': 'Ecotourism planning and management',
        'priority': 'P4'
    },
    'engine/hydroma/web_search': {
        'name': 'web_search',
        'class': 'WebSearch',
        'description': 'Web search and information retrieval',
        'priority': 'P4'
    },
    'engine/hydroma/data_ingestion': {
        'name': 'data_ingestion',
        'class': 'DataIngestion',
        'description': 'Data ingestion and preprocessing',
        'priority': 'P2'
    },
    'engine/hydroma/standards': {
        'name': 'standards',
        'class': 'Standards',
        'description': 'Standards and compliance management',
        'priority': 'P3'
    },
    # Services
    'services/auth': {
        'name': 'auth',
        'class': 'Auth',
        'description': 'Authentication and authorization service',
        'priority': 'P1'
    },
    'services/ledger': {
        'name': 'ledger',
        'class': 'Ledger',
        'description': 'Transaction ledger service',
        'priority': 'P2'
    },
    'services/notification': {
        'name': 'notification',
        'class': 'Notification',
        'description': 'Notification service',
        'priority': 'P2'
    },
    'services/reporting': {
        'name': 'reporting',
        'class': 'Reporting',
        'description': 'Report generation service',
        'priority': 'P3'
    },
    'services/workflow': {
        'name': 'workflow',
        'class': 'Workflow',
        'description': 'Workflow management service',
        'priority': 'P3'
    },
}


class StructureSetup:
    """Setup standard structure for all modules."""
    
    def __init__(self, dry_run: bool = True, create_templates: bool = False):
        self.dry_run = dry_run
        self.create_templates = create_templates
        self.stats = {
            'modules_processed': 0,
            'files_created': 0,
            'files_existing': 0,
            'natural_placeholders': 0,
            'real_placeholders': 0
        }
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'modules': {},
            'natural_placeholders': [],
            'actions': []
        }
    
    def setup_module(self, module_path: str, config: Dict) -> None:
        """Setup standard structure for a module."""
        full_path = PROJECT_ROOT / module_path
        
        print(f"\n📦 Setting up: {module_path}")
        
        # Create directory if not exists
        if not full_path.exists():
            if not self.dry_run:
                full_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created directory")
        else:
            print(f"  ℹ Directory exists")
        
        # Prepare template variables
        module_name = config['name']
        module_class = config['class']
        module_description = config['description']
        module_path_str = module_path.replace('/', '.')
        
        template_vars = {
            'module_name': module_name,
            'module_class': module_class,
            'module_description': module_description,
            'module_path': module_path_str,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Create files
        for filename, template in STANDARD_STRUCTURE.items():
            file_path = full_path / filename
            
            # Create parent directory for tests
            if '/' in filename:
                parent = full_path / Path(filename).parent
                if not parent.exists() and not self.dry_run:
                    parent.mkdir(parents=True, exist_ok=True)
            
            if file_path.exists():
                # Check if it's an empty __init__.py (natural placeholder)
                if filename == '__init__.py':
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if len(content.strip()) < 50:
                        self.stats['natural_placeholders'] += 1
                        self.report['natural_placeholders'].append(str(file_path.relative_to(PROJECT_ROOT)))
                        print(f"  ℹ Natural placeholder: {filename}")
                    else:
                        self.stats['files_existing'] += 1
                        print(f"  ℹ Existing file: {filename}")
                else:
                    self.stats['files_existing'] += 1
                    print(f"  ℹ Existing file: {filename}")
                continue
            
            # Create new file
            if not self.dry_run:
                try:
                    content = template.format(**template_vars)
                    file_path.write_text(content, encoding='utf-8')
                    self.stats['files_created'] += 1
                    print(f"  ✓ Created: {filename}")
                except Exception as e:
                    print(f"  ✗ Error creating {filename}: {e}")
            else:
                print(f"  → Would create: {filename}")
        
        self.stats['modules_processed'] += 1
        self.report['modules'][module_path] = {
            'name': module_name,
            'priority': config['priority'],
            'status': 'setup_complete' if not self.dry_run else 'dry_run'
        }
    
    def run(self) -> None:
        """Execute setup for all modules."""
        print("\n" + "="*70)
        print("  ECO NOJIN - STANDARD STRUCTURE SETUP")
        print("="*70)
        print(f"\n  Mode: {'DRY RUN' if self.dry_run else 'CREATE'}")
        print(f"  Create templates: {self.create_templates}")
        print(f"  Modules to process: {len(MODULES)}")
        
        for module_path, config in MODULES.items():
            self.setup_module(module_path, config)
        
        # Generate reports
        self._generate_reports()
        
        # Print summary
        print("\n" + "="*70)
        print("  SETUP COMPLETE")
        print("="*70)
        print(f"\n  Modules processed: {self.stats['modules_processed']}")
        print(f"  Files created: {self.stats['files_created']}")
        print(f"  Files existing: {self.stats['files_existing']}")
        print(f"  Natural placeholders: {self.stats['natural_placeholders']}")
        print(f"\n📄 Reports:")
        print(f"   • {REPORT_FILE}")
        print(f"   • {REPORT_MD}")
    
    def _generate_reports(self) -> None:
        """Generate JSON and Markdown reports."""
        # JSON report
        report_data = {
            **self.report,
            'statistics': self.stats
        }
        REPORT_FILE.write_text(
            json.dumps(report_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        # Markdown report
        md = self._generate_markdown_report()
        REPORT_MD.write_text(md, encoding='utf-8')
    
    def _generate_markdown_report(self) -> str:
        """Generate Markdown report."""
        md = []
        md.append("# 🏗️ Structure Setup Report")
        md.append(f"\n**Generated:** {self.report['timestamp']}")
        md.append(f"**Mode:** {'DRY RUN' if self.dry_run else 'CREATE'}")
        
        md.append("\n## 📊 Statistics\n")
        md.append(f"- **Modules Processed:** {self.stats['modules_processed']}")
        md.append(f"- **Files Created:** {self.stats['files_created']}")
        md.append(f"- **Files Existing:** {self.stats['files_existing']}")
        md.append(f"- **Natural Placeholders:** {self.stats['natural_placeholders']}")
        
        md.append("\n## 📦 Module Status\n")
        md.append("| Module | Priority | Status |")
        md.append("|--------|----------|--------|")
        
        for module_path, info in self.report['modules'].items():
            status_emoji = '✅' if info['status'] == 'setup_complete' else '🔄'
            md.append(f"| `{module_path}` | {info['priority']} | {status_emoji} {info['status']} |")
        
        md.append("\n## ℹ️ Natural Placeholders (No Action Needed)\n")
        md.append("These are `__init__.py` files that are intentionally empty:\n")
        for placeholder in self.report['natural_placeholders'][:20]:
            md.append(f"- `{placeholder}`")
        
        return "\n".join(md)


if __name__ == '__main__':
    import sys
    
    dry_run = '--create-templates' not in sys.argv
    
    if dry_run:
        print("\nℹ️  Running in DRY RUN mode (no files created)")
        print("   Use --create-templates to actually create files\n")
    
    setup = StructureSetup(dry_run=dry_run, create_templates=True)
    setup.run()