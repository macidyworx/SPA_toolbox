"""
clean_field.py
Reusable text normalization utility for robust cell/text comparison.
"""
import unicodedata
import re

_ws_re = re.compile(r'\s+')

def field_cleaner(text, lowercase=True, collapse_whitespace=True, strip_spaces=True, strip_bom=True, unicode_form='NFKC'):
    """
    Normalize text for robust comparison:
    - Unicode normalization (NFKC by default, also handles Roman numerals and fullwidth forms)
    - Replace all unicode whitespace with ASCII space
    - Collapse multiple spaces
    - Optionally remove all spaces (for matching "Van Owen" to "Vanowen")
    - Lowercase (optional)
    - Strip leading/trailing whitespace
    - Remove BOM (optional, anywhere in string)
    - Replace em dash and en dash with hyphen (-)
    - Replace ß with ss

    Args:
        text (str): Input text to normalize.
        lowercase (bool): Convert to lowercase if True.
        collapse_whitespace (bool): Collapse multiple whitespace to single space if True.
        strip_spaces (bool): Remove all spaces if True. Use for matching names/IDs
                             where spacing varies (e.g. "Van Owen" vs "Vanowen").
        strip_bom (bool): Remove BOM if present.
        unicode_form (str): Unicode normalization form (e.g., 'NFKC', 'NFC').

    Returns:
        str: Normalized text.
    """
    if text is None:
        return ''
    text = str(text)
    if strip_bom:
        text = text.replace('\ufeff', '')
    text = unicodedata.normalize(unicode_form, text)
    text = text.replace('—', '-').replace('–', '-')
    text = text.replace('ß', 'ss')
    text = ''.join(' ' if unicodedata.category(c).startswith('Z') or c in '\t\n\r\f\v' else c for c in text)
    if lowercase:
        text = text.lower()
    if strip_spaces:
        text = text.replace(' ', '')
    elif collapse_whitespace:
        text = _ws_re.sub(' ', text)
    return text.strip()
