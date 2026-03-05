"""
clean_field.py
Reusable text normalization utility for robust cell/text comparison.
"""
import unicodedata
import re

_ws_re = re.compile(r'\s+')

def field_cleaner(text, lowercase=True, collapse_whitespace=True, strip_bom=True, unicode_form='NFKC'):
    """
    Normalize text for robust comparison:
    - Unicode normalization (NFKC by default)
    - Replace all unicode whitespace with ASCII space
    - Collapse multiple spaces
    - Lowercase (optional)
    - Strip leading/trailing whitespace
    - Remove BOM (optional, anywhere in string)
    - Replace em dash (—) with hyphen (-)
    - Replace ß with ss
    - Normalize Roman numerals and fullwidth forms

    Args:
        text (str): Input text to normalize.
        lowercase (bool): Convert to lowercase if True.
        collapse_whitespace (bool): Collapse multiple whitespace to single space if True.
        strip_bom (bool): Remove BOM if present.
        unicode_form (str): Unicode normalization form (e.g., 'NFKC', 'NFC').

    Returns:
        str: Normalized text.
    """
    if text is None:
        return ''
    text = str(text)
    if strip_bom:
        text = text.replace('\ufeff', '')  # Remove BOM anywhere
    text = unicodedata.normalize(unicode_form, text)
    # Replace em dash and en dash with hyphen
    text = text.replace('—', '-').replace('–', '-')
    # Replace ß with ss (after normalization)
    text = text.replace('ß', 'ss')
    # Roman numerals (common ones)
    roman_map = {
        'Ⅰ': '1', 'Ⅱ': '2', 'Ⅲ': '3', 'Ⅳ': 'iv', 'Ⅴ': 'v', 'Ⅵ': 'vi', 'Ⅶ': 'vii', 'Ⅷ': 'viii', 'Ⅸ': 'ix', 'Ⅹ': 'x',
        'Ⅺ': 'xi', 'Ⅻ': 'xii', 'Ⅼ': 'l', 'Ⅽ': 'c', 'Ⅾ': 'd', 'Ⅿ': 'm',
        'ⅰ': '1', 'ⅱ': '2', 'ⅲ': '3', 'ⅳ': 'iv', 'ⅴ': 'v', 'ⅵ': 'vi', 'ⅶ': 'vii', 'ⅷ': 'viii', 'ⅸ': 'ix', 'ⅹ': 'x',
        'ⅺ': 'xi', 'ⅻ': 'xii', 'ⅼ': 'l', 'ⅽ': 'c', 'ⅾ': 'd', 'ⅿ': 'm',
    }
    text = ''.join(roman_map.get(c, c) for c in text)
    text = ''.join(' ' if unicodedata.category(c).startswith('Z') or c in '\t\n\r\f\v' else c for c in text)
    if lowercase:
        text = text.lower()
    if collapse_whitespace:
        text = _ws_re.sub(' ', text)
    return text.strip()
