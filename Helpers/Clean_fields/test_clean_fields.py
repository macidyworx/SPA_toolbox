import pytest
from Helpers.Clean_fields.clean_field import field_cleaner

# Default behavior (strip_spaces=True)
default_cases = [
    # Simple
    ("", ""),
    ("   leading and trailing   ", "leadingandtrailing"),
    ("MiXeD CaSe", "mixedcase"),

    # BOM
    ("\ufeffHello World", "helloworld"),
    ("\ufeff   spaced text", "spacedtext"),

    # Unicode whitespace
    ("Hello\u00A0World", "helloworld"),
    ("Line\nbreak", "linebreak"),
    ("Tab\tseparated", "tabseparated"),
    ("Weird space types", "weirdspacetypes"),

    # Multiple whitespace collapsing (all removed by default)
    ("A     lot     of    spaces", "alotofspaces"),
    ("Mix\t of \n whitespace", "mixofwhitespace"),

    # Unicode normalization (NFKC handles circled digits and fullwidth)
    ("①②③", "123"),
    ("ⅣⅤⅥ", "ivvvi"),
    ("ℌ𝔢𝔩𝔩𝔬", "hello"),
    ("ｆｕｌｌｗｉｄｔｈ", "fullwidth"),

    # Accents + decomposition
    ("café", "café"),
    ("cafe\u0301", "café"),
    ("Ångström", "ångström"),
    ("A\u030Angstro\u0308m", "ångström"),

    # Dashes
    ("Hello—world", "hello-world"),
    ("Price: 10 000", "price:10000"),

    # Lowercasing check
    ("THIS SHOULD BECOME LOWERCASE", "thisshouldbecomelowercase"),
    ("ß", "ss"),

    # Mixed garbage
    ("  \t  \ufeff  weird text　here  ", "weirdtexthere"),

    # Emoji should remain unchanged
    ("Text🧪WithEmoji", "text🧪withemoji"),

    # None -> empty string
    (None, ""),

    # Name/ID matching (default strips spaces)
    ("Van Owen", "vanowen"),
    ("Vanowen", "vanowen"),
    ("  De La Cruz  ", "delacruz"),
    ("abc 0001", "abc0001"),
    ("ABC0001", "abc0001"),
    ("  \t  spaced\tout  ", "spacedout"),
]


@pytest.mark.parametrize("input_text, expected", default_cases)
def test_field_cleaner_default(input_text, expected):
    assert field_cleaner(input_text) == expected


# strip_spaces=False: preserve spaces, collapse whitespace
preserve_spaces_cases = [
    ("", ""),
    ("   leading and trailing   ", "leading and trailing"),
    ("MiXeD CaSe", "mixed case"),
    ("\ufeffHello World", "hello world"),
    ("Hello\u00A0World", "hello world"),
    ("A     lot     of    spaces", "a lot of spaces"),
    ("Mix\t of \n whitespace", "mix of whitespace"),
    ("Hello—world", "hello-world"),
    ("Price: 10 000", "price: 10 000"),
    ("  \t  \ufeff  weird text　here  ", "weird text here"),
    (None, ""),
]


@pytest.mark.parametrize("input_text, expected", preserve_spaces_cases)
def test_field_cleaner_preserve_spaces(input_text, expected):
    assert field_cleaner(input_text, strip_spaces=False) == expected
