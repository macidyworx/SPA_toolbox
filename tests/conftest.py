"""
Shared pytest fixtures and configuration for SPA_toolbox tests.
"""

import pytest
from pathlib import Path
import sys

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def tmp_xlsx(tmp_path):
    """Create a temporary Excel file for testing."""
    try:
        import openpyxl
        xlsx_path = tmp_path / "test.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Header1", "Header2"])
        ws.append(["Value1", "Value2"])
        wb.save(xlsx_path)
        wb.close()
        return xlsx_path
    except ImportError:
        pytest.skip("openpyxl not available")
