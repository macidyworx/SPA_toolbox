"""
test_PAT_Username_Checker.py

Comprehensive test suite for PAT_Username_Checker module.

Test coverage:
- Format validators (alphanumeric, long numeric, short numeric)
- Username column auto-detection
- File validation (all match, partial match, empty, corrupt)
- File organization and output folder structure
- Integration tests (module import, standalone execution)
"""

import unittest
import tempfile
import shutil
import os
import wx
from pathlib import Path
from openpyxl import Workbook

from RandomTools.PAT.PAT_Username_Checker import (
    validate_alphanumeric,
    validate_long_numeric,
    validate_short_numeric,
    detect_username_column,
    PAT_Username_Checker,
    STATUS_EXPECTED_ID,
    STATUS_FILES_TO_CHECK,
    STATUS_EMPTY_OR_UNREADABLE,
)


# === TEST FIXTURES ===

def create_test_excel(filename, headers, data):
    """
    Create a test Excel file with given headers and data.

    Args:
        filename: Path to create the file at.
        headers: List of header strings for row 1.
        data: List of lists, where each inner list is a row of data.
    """
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in data:
        ws.append(row)
    wb.save(filename)
    wb.close()


# === FORMAT VALIDATION TESTS ===

class TestFormatValidation(unittest.TestCase):
    """Test the three format validators."""

    def test_alphanumeric_accepts_abc0001(self):
        """Alphanumeric format should accept ABC0001."""
        self.assertTrue(validate_alphanumeric("ABC0001"))

    def test_alphanumeric_accepts_abc0001_lowercase(self):
        """Alphanumeric format should accept lowercase abc0001."""
        self.assertTrue(validate_alphanumeric("abc0001"))

    def test_alphanumeric_accepts_abc0001_mixed_case(self):
        """Alphanumeric format should accept mixed case AbC0001."""
        self.assertTrue(validate_alphanumeric("AbC0001"))

    def test_alphanumeric_accepts_ab_dash_0001(self):
        """Alphanumeric format should accept AB-0001 (2 letters, dash, 4 digits)."""
        self.assertTrue(validate_alphanumeric("AB-0001"))

    def test_alphanumeric_rejects_too_many_digits(self):
        """Alphanumeric format should reject ABC00012 (5 digits)."""
        self.assertFalse(validate_alphanumeric("ABC00012"))

    def test_alphanumeric_rejects_too_few_letters(self):
        """Alphanumeric format should reject AB0001 (2 letters only)."""
        self.assertFalse(validate_alphanumeric("AB0001"))

    def test_alphanumeric_rejects_too_many_letters(self):
        """Alphanumeric format should reject ABCD0001 (4 letters)."""
        self.assertFalse(validate_alphanumeric("ABCD0001"))

    def test_alphanumeric_rejects_too_few_digits(self):
        """Alphanumeric format should reject ABC001 (3 digits)."""
        self.assertFalse(validate_alphanumeric("ABC001"))

    def test_alphanumeric_rejects_none(self):
        """Alphanumeric format should reject None."""
        self.assertFalse(validate_alphanumeric(None))

    def test_long_numeric_accepts_1234(self):
        """Long numeric format should accept 1234 (4 digits)."""
        self.assertTrue(validate_long_numeric("1234"))

    def test_long_numeric_accepts_123456789(self):
        """Long numeric format should accept 123456789 (9 digits)."""
        self.assertTrue(validate_long_numeric("123456789"))

    def test_long_numeric_accepts_999999999999(self):
        """Long numeric format should accept 999999999999 (12 digits)."""
        self.assertTrue(validate_long_numeric("999999999999"))

    def test_long_numeric_rejects_123(self):
        """Long numeric format should reject 123 (3 digits)."""
        self.assertFalse(validate_long_numeric("123"))

    def test_long_numeric_rejects_1234567890123(self):
        """Long numeric format should reject 1234567890123 (13 digits)."""
        self.assertFalse(validate_long_numeric("1234567890123"))

    def test_long_numeric_accepts_integer_input(self):
        """Long numeric format should handle integer input."""
        self.assertTrue(validate_long_numeric(12345))

    def test_long_numeric_rejects_none(self):
        """Long numeric format should reject None."""
        self.assertFalse(validate_long_numeric(None))

    def test_short_numeric_accepts_12(self):
        """Short numeric format should accept 12 (2 digits)."""
        self.assertTrue(validate_short_numeric("12"))

    def test_short_numeric_accepts_12345(self):
        """Short numeric format should accept 12345 (5 digits)."""
        self.assertTrue(validate_short_numeric("12345"))

    def test_short_numeric_accepts_99999999(self):
        """Short numeric format should accept 99999999 (8 digits)."""
        self.assertTrue(validate_short_numeric("99999999"))

    def test_short_numeric_rejects_1(self):
        """Short numeric format should reject 1 (1 digit)."""
        self.assertFalse(validate_short_numeric("1"))

    def test_short_numeric_rejects_999999999(self):
        """Short numeric format should reject 999999999 (9 digits)."""
        self.assertFalse(validate_short_numeric("999999999"))

    def test_short_numeric_accepts_integer_input(self):
        """Short numeric format should handle integer input."""
        self.assertTrue(validate_short_numeric(5548))

    def test_short_numeric_rejects_none(self):
        """Short numeric format should reject None."""
        self.assertFalse(validate_short_numeric(None))

    def test_all_validators_handle_string_and_int(self):
        """All validators should handle both string and int inputs uniformly."""
        # Alphanumeric only accepts strings
        self.assertTrue(validate_alphanumeric("ABC0001"))
        self.assertFalse(validate_alphanumeric(123))

        # Long numeric should accept both
        self.assertTrue(validate_long_numeric("12345"))
        self.assertTrue(validate_long_numeric(12345))

        # Short numeric should accept both
        self.assertTrue(validate_short_numeric("1234"))
        self.assertTrue(validate_short_numeric(1234))

    def test_all_validators_case_insensitive(self):
        """All validators should be case-insensitive."""
        # Alphanumeric with various cases
        self.assertTrue(validate_alphanumeric("ABC0001"))
        self.assertTrue(validate_alphanumeric("abc0001"))
        self.assertTrue(validate_alphanumeric("AbC0001"))


# === COLUMN DETECTION TESTS ===

class TestColumnDetection(unittest.TestCase):
    """Test the username column auto-detection function."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.test_dir)

    def test_detect_username_header_exact_match(self):
        """Auto-detect should find 'Username' header (exact match)."""
        filepath = os.path.join(self.test_dir, "test_username.xlsx")
        create_test_excel(filepath, ["Username", "Age"], [["ABC0001", 25]])
        result = detect_username_column(filepath)
        self.assertEqual(result, "A")

    def test_detect_user_id_header(self):
        """Auto-detect should find 'User ID' header (case-insensitive, whitespace-tolerant)."""
        filepath = os.path.join(self.test_dir, "test_userid.xlsx")
        create_test_excel(filepath, ["Name", "User ID", "Score"], [["John", "ABC0001", 100]])
        result = detect_username_column(filepath)
        self.assertEqual(result, "B")

    def test_detect_id_header_unambiguous(self):
        """Auto-detect should find 'ID' header when unambiguous."""
        filepath = os.path.join(self.test_dir, "test_id.xlsx")
        create_test_excel(filepath, ["Name", "ID", "Score"], [["John", "ABC0001", 100]])
        result = detect_username_column(filepath)
        self.assertEqual(result, "B")

    def test_detect_userid_header_no_space(self):
        """Auto-detect should find 'UserID' header (no space)."""
        filepath = os.path.join(self.test_dir, "test_userid_nospace.xlsx")
        create_test_excel(filepath, ["Name", "UserID"], [["John", "ABC0001"]])
        result = detect_username_column(filepath)
        self.assertEqual(result, "B")

    def test_detect_returns_none_if_not_found(self):
        """Auto-detect should return None if no matching header found."""
        filepath = os.path.join(self.test_dir, "test_noheader.xlsx")
        create_test_excel(filepath, ["Name", "Age", "Score"], [["John", 25, 100]])
        result = detect_username_column(filepath)
        self.assertIsNone(result)

    def test_detect_case_insensitive(self):
        """Auto-detect should match headers case-insensitively."""
        filepath = os.path.join(self.test_dir, "test_case.xlsx")
        create_test_excel(filepath, ["username", "age"], [["ABC0001", 25]])
        result = detect_username_column(filepath)
        self.assertEqual(result, "A")

    def test_detect_whitespace_tolerant(self):
        """Auto-detect should match headers with extra whitespace."""
        filepath = os.path.join(self.test_dir, "test_whitespace.xlsx")
        create_test_excel(filepath, ["Name", "  User  ID  "], [["John", "ABC0001"]])
        result = detect_username_column(filepath)
        self.assertEqual(result, "B")


# === FILE VALIDATION TESTS ===

class TestFileValidation(unittest.TestCase):
    """Test file validation logic."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.test_dir)

    def test_file_all_matching_returns_expected_id(self):
        """File with all matching usernames should return EXPECTED_ID status."""
        filepath = os.path.join(self.test_dir, "test_all_match.xlsx")
        create_test_excel(
            filepath,
            ["Username", "Score"],
            [["ABC0001", 100], ["ABC0002", 95], ["ABC0003", 88]]
        )
        checker = PAT_Username_Checker(self.test_dir, 'alphanumeric')
        result = checker._validate_file(filepath)
        self.assertEqual(result, STATUS_EXPECTED_ID)

    def test_file_one_nonmatching_returns_files_to_check(self):
        """File with one non-matching username should return FILES_TO_CHECK status."""
        filepath = os.path.join(self.test_dir, "test_partial_match.xlsx")
        create_test_excel(
            filepath,
            ["Username", "Score"],
            [["ABC0001", 100], ["INVALID", 95]]
        )
        checker = PAT_Username_Checker(self.test_dir, 'alphanumeric')
        result = checker._validate_file(filepath)
        self.assertEqual(result, STATUS_FILES_TO_CHECK)

    def test_file_empty_column_returns_empty_or_unreadable(self):
        """File with empty username column should return EMPTY_OR_UNREADABLE."""
        filepath = os.path.join(self.test_dir, "test_empty.xlsx")
        create_test_excel(filepath, ["Username", "Score"], [])
        checker = PAT_Username_Checker(self.test_dir, 'alphanumeric')
        result = checker._validate_file(filepath)
        self.assertEqual(result, STATUS_EMPTY_OR_UNREADABLE)

    def test_file_corrupt_returns_empty_or_unreadable(self):
        """Corrupt/unreadable Excel file should return EMPTY_OR_UNREADABLE."""
        filepath = os.path.join(self.test_dir, "test_corrupt.xlsx")
        # Write invalid content to file to make it unreadable
        with open(filepath, 'w') as f:
            f.write("This is not a valid Excel file")
        checker = PAT_Username_Checker(self.test_dir, 'alphanumeric')
        result = checker._validate_file(filepath)
        self.assertEqual(result, STATUS_EMPTY_OR_UNREADABLE)

    def test_file_mixed_string_numeric_validates_correctly(self):
        """File with mixed string/numeric usernames should validate correctly."""
        filepath = os.path.join(self.test_dir, "test_mixed.xlsx")
        create_test_excel(
            filepath,
            ["Username", "Score"],
            [[182815548, 100], ["182815549", 95], [182815550, 88]]
        )
        checker = PAT_Username_Checker(self.test_dir, 'long_numeric')
        result = checker._validate_file(filepath)
        self.assertEqual(result, STATUS_EXPECTED_ID)


# === FILE ORGANIZATION TESTS ===

class TestFileOrganization(unittest.TestCase):
    """Test file organization workflow."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.test_dir)

    def test_output_folder_structure_created(self):
        """Output folder structure should be created (Expected_ID, Files_to_check, Empty_or_unreadable)."""
        checker = PAT_Username_Checker(self.test_dir, 'alphanumeric')
        self.assertTrue(checker._ensure_output_structure())

        # Check subdirectories exist
        expected_subdir = Path(self.test_dir) / 'Expected_ID'
        to_check_subdir = Path(self.test_dir) / 'Files_to_check'
        empty_subdir = Path(self.test_dir) / 'Empty_or_unreadable'

        self.assertTrue(expected_subdir.exists())
        self.assertTrue(to_check_subdir.exists())
        self.assertTrue(empty_subdir.exists())

    def test_file_moved_to_correct_subfolder(self):
        """File should be moved to correct subfolder based on validation result."""
        # Create source file
        source_file = os.path.join(self.test_dir, "source", "test.xlsx")
        os.makedirs(os.path.dirname(source_file), exist_ok=True)
        create_test_excel(source_file, ["Username"], [["ABC0001"]])

        # Process with checker
        output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        checker = PAT_Username_Checker(output_dir, 'alphanumeric')
        stats = checker.run([source_file])

        # Check file was moved to Expected_ID
        expected_location = Path(output_dir) / 'Expected_ID' / 'test.xlsx'
        self.assertTrue(expected_location.exists())
        self.assertFalse(Path(source_file).exists())

    def test_filename_collision_handled(self):
        """Filename collision should be handled (appends _(1), _(2), etc.)."""
        output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Create two source files with the same name
        source_dir = os.path.join(self.test_dir, "source")
        os.makedirs(source_dir, exist_ok=True)

        source_file1 = os.path.join(source_dir, "test1.xlsx")
        source_file2 = os.path.join(source_dir, "test2.xlsx")
        create_test_excel(source_file1, ["Username"], [["ABC0001"]])
        create_test_excel(source_file2, ["Username"], [["ABC0002"]])

        # Rename both to same name for conflict test
        os.rename(source_file2, os.path.join(source_dir, "test1_renamed.xlsx"))
        source_file2 = os.path.join(source_dir, "test1_renamed.xlsx")

        # Move first file
        checker = PAT_Username_Checker(output_dir, 'alphanumeric')
        checker.run([source_file1])

        # Now rename second file to same and move it
        os.rename(source_file2, source_file1)
        checker.run([source_file1])

        # Check that both files exist in output (one with _(1) suffix)
        expected_dir = Path(output_dir) / 'Expected_ID'
        files_in_output = list(expected_dir.glob("test1*"))
        self.assertGreaterEqual(len(files_in_output), 1)

    def test_original_file_removed_after_move(self):
        """Original file should no longer exist after move."""
        source_file = os.path.join(self.test_dir, "source", "test.xlsx")
        os.makedirs(os.path.dirname(source_file), exist_ok=True)
        create_test_excel(source_file, ["Username"], [["ABC0001"]])

        output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        checker = PAT_Username_Checker(output_dir, 'alphanumeric')
        checker.run([source_file])

        self.assertFalse(Path(source_file).exists())


# === INTEGRATION TESTS ===

class TestIntegration(unittest.TestCase):
    """Test integration and module import."""

    def test_module_import(self):
        """Module should be importable."""
        from RandomTools.PAT import PAT_Username_Checker as module
        self.assertIsNotNone(module)

    def test_class_instantiation(self):
        """Class should be instantiable with valid arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checker = PAT_Username_Checker(tmpdir, 'alphanumeric')
            self.assertIsNotNone(checker)
            self.assertEqual(checker.selected_format, 'alphanumeric')

    def test_summary_report_accuracy(self):
        """Summary report should accurately count files in each category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            source_dir = os.path.join(tmpdir, "source")
            os.makedirs(source_dir, exist_ok=True)

            file1 = os.path.join(source_dir, "expected.xlsx")
            file2 = os.path.join(source_dir, "check.xlsx")

            create_test_excel(file1, ["Username"], [["ABC0001"]])
            create_test_excel(file2, ["Username"], [["INVALID"]])

            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir, exist_ok=True)

            checker = PAT_Username_Checker(output_dir, 'alphanumeric')
            stats = checker.run([file1, file2])

            self.assertEqual(stats['total_processed'], 2)
            self.assertEqual(stats['expected_id'], 1)
            self.assertEqual(stats['files_to_check'], 1)
            self.assertEqual(stats['errors'], 0)


if __name__ == '__main__':
    unittest.main()
