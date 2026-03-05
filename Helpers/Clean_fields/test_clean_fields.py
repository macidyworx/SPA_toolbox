import pytest
from tool_box.Clean_fields.clean_field import clean_cell

test_cases = [
    # Simple
    ("", ""),
    ("   leading and trailing   ", "leading and trailing"),
    ("MiXeD CaSe", "mixed case"),

    # BOM
    ("\ufeffHello World", "hello world"),
    ("\ufeff   spaced text", "spaced text"),

    # Unicode whitespace
    ("Hello\u00A0World", "hello world"),
    ("Line\nbreak", "line break"),
    ("Tab\tseparated", "tab separated"),
    ("Weird space types", "weird space types"),

    # Multiple whitespace collapsing
    ("A     lot     of    spaces", "a lot of spaces"),
    ("Mix\t of \n whitespace", "mix of whitespace"),

    # Unicode normalization
    ("①②③", "123"),
    ("ⅣⅤⅥ", "ivvvi"),     # NFKC and mapping: Ⅳ→iv, Ⅴ→v, Ⅵ→vi
    ("ℌ𝔢𝔩𝔩𝔬", "hello"),
    ("ｆｕｌｌｗｉｄｔｈ", "fullwidth"),

    # Accents + decomposition
    ("café", "café"),
    ("cafe\u0301", "café"),
    ("Ångström", "ångström"),
    ("A\u030Angstro\u0308m", "ångström"),

    # Dashes and spaces
    ("Hello—world", "hello-world"),
    ("Price: 10 000", "price: 10 000"),

    # Lowercasing check
    ("THIS SHOULD BECOME LOWERCASE", "this should become lowercase"),
    ("ß", "ss"),  # NFKC converts ß -> ss

    # Mixed garbage
    ("  \t  \ufeff  weird text　here  ", "weird text here"),

    # Emoji should remain unchanged
    ("Text🧪WithEmoji", "text🧪withemoji"),  # only whitespace/lowercase normalize

    # None → empty string
    (None, ""),
]


@pytest.mark.parametrize("input_text, expected", test_cases)
def test_clean_cell(input_text, expected):
    assert clean_cell(input_text) == expected
