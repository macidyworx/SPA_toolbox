"""
Tests for cell_utils.py
"""

import pytest

from Finders.File_sorter.cell_utils import parse_cell_ref, _col_letters_to_number


# === TESTS: parse_cell_ref ===

class TestParseCellRef:
    """Tests for parse_cell_ref function."""

    def test_a1(self):
        assert parse_cell_ref("A1") == (1, 1)

    def test_b2(self):
        assert parse_cell_ref("B2") == (2, 2)

    def test_c1(self):
        assert parse_cell_ref("C1") == (1, 3)

    def test_f1(self):
        assert parse_cell_ref("F1") == (1, 6)

    def test_g1(self):
        assert parse_cell_ref("G1") == (1, 7)

    def test_h2(self):
        assert parse_cell_ref("H2") == (2, 8)

    def test_i1(self):
        assert parse_cell_ref("I1") == (1, 9)

    def test_j1(self):
        assert parse_cell_ref("J1") == (1, 10)

    def test_k1(self):
        assert parse_cell_ref("K1") == (1, 11)

    def test_l1(self):
        assert parse_cell_ref("L1") == (1, 12)

    def test_z1(self):
        assert parse_cell_ref("Z1") == (1, 26)

    def test_lowercase(self):
        """Lowercase cell refs are handled."""
        assert parse_cell_ref("a1") == (1, 1)
        assert parse_cell_ref("b2") == (2, 2)

    def test_mixed_case(self):
        """Mixed case cell refs are handled."""
        assert parse_cell_ref("aA1") == (1, 27)

    def test_aa1(self):
        """Multi-letter column AA = 27."""
        assert parse_cell_ref("AA1") == (1, 27)

    def test_ab1(self):
        """Multi-letter column AB = 28."""
        assert parse_cell_ref("AB1") == (1, 28)

    def test_az1(self):
        """Multi-letter column AZ = 52."""
        assert parse_cell_ref("AZ1") == (1, 52)

    def test_ba1(self):
        """Multi-letter column BA = 53."""
        assert parse_cell_ref("BA1") == (1, 53)

    def test_large_row(self):
        """Large row numbers work."""
        assert parse_cell_ref("A100") == (100, 1)

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped."""
        assert parse_cell_ref("  A1  ") == (1, 1)

    def test_invalid_empty(self):
        with pytest.raises(ValueError, match="Invalid cell reference"):
            parse_cell_ref("")

    def test_invalid_no_row(self):
        with pytest.raises(ValueError, match="Invalid cell reference"):
            parse_cell_ref("A")

    def test_invalid_no_col(self):
        with pytest.raises(ValueError, match="Invalid cell reference"):
            parse_cell_ref("1")

    def test_invalid_number_first(self):
        with pytest.raises(ValueError, match="Invalid cell reference"):
            parse_cell_ref("1A")

    def test_invalid_special_chars(self):
        with pytest.raises(ValueError, match="Invalid cell reference"):
            parse_cell_ref("A$1")

    def test_invalid_not_string(self):
        with pytest.raises(ValueError, match="must be a string"):
            parse_cell_ref(42)

    def test_invalid_list(self):
        with pytest.raises(ValueError, match="must be a string"):
            parse_cell_ref([0, 0])


# === TESTS: _col_letters_to_number ===

class TestColLettersToNumber:
    """Tests for column letter conversion."""

    def test_single_letters(self):
        assert _col_letters_to_number("A") == 1
        assert _col_letters_to_number("B") == 2
        assert _col_letters_to_number("Z") == 26

    def test_double_letters(self):
        assert _col_letters_to_number("AA") == 27
        assert _col_letters_to_number("AB") == 28
        assert _col_letters_to_number("AZ") == 52
        assert _col_letters_to_number("BA") == 53

    def test_triple_letters(self):
        assert _col_letters_to_number("AAA") == 703
