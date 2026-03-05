import pytest
import openpyxl
from Helpers.dog_box.ssotsif import _validate_sif, SIF_HEADERS


# --- SIF validation tests (no wx needed) ---

def _make_sif(path, row2_values):
    """Create an xlsx with row 1 blank and row 2 set to given values."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append([None])  # row 1 blank
    ws.append(row2_values)  # row 2 headers
    ws.append(["2024", "7", "Smith", "John", "12345"])  # row 3 sample data
    wb.save(path)
    wb.close()


def test_valid_sif(tmp_path):
    path = tmp_path / "good_sif.xlsx"
    _make_sif(path, ["CalendarYear", "YearLevel", "Surname", "Firstname", "StudentID"])
    _validate_sif(str(path))  # should not raise


def test_valid_sif_case_insensitive(tmp_path):
    path = tmp_path / "case_sif.xlsx"
    _make_sif(path, ["calendaryear", "YEARLEVEL", "Surname", "firstname", "studentid"])
    _validate_sif(str(path))  # should not raise


def test_invalid_sif_wrong_header(tmp_path):
    path = tmp_path / "bad_sif.xlsx"
    _make_sif(path, ["CalendarYear", "Grade", "Surname", "Firstname", "StudentID"])
    with pytest.raises(ValueError, match="YearLevel"):
        _validate_sif(str(path))


def test_invalid_sif_missing_headers(tmp_path):
    path = tmp_path / "empty_sif.xlsx"
    _make_sif(path, [None, None, None, None, None])
    with pytest.raises(ValueError, match="CalendarYear"):
        _validate_sif(str(path))


def test_invalid_sif_empty_row2(tmp_path):
    """File with no row 2 data at all."""
    path = tmp_path / "no_row2.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Title row"])
    # row 2 is completely empty
    wb.save(path)
    wb.close()
    with pytest.raises(ValueError, match="SIF header validation failed"):
        _validate_sif(str(path))


def test_invalid_sif_extra_whitespace(tmp_path):
    """Headers with extra whitespace should still match."""
    path = tmp_path / "ws_sif.xlsx"
    _make_sif(path, ["  CalendarYear ", " YearLevel", "Surname  ", " Firstname ", " StudentID "])
    _validate_sif(str(path))  # should not raise


def test_invalid_sif_swapped_columns(tmp_path):
    """Headers in wrong column positions should fail."""
    path = tmp_path / "swapped_sif.xlsx"
    _make_sif(path, ["Surname", "Firstname", "CalendarYear", "YearLevel", "StudentID"])
    with pytest.raises(ValueError, match="CalendarYear"):
        _validate_sif(str(path))
