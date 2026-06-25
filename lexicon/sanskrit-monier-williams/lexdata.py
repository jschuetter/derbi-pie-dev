"""
lexdata.py
Script for retrieving additional lexical information
N.B. CLTK lacks a Sanskrit IPA transcription module
(e.g. phonetic transcription, transliteration, etc.)
"""

import re
from indic_transliteration.sanscript import transliterate, SLP1, IAST, DEVANAGARI

IAST_REGEXP = r'[A-Za-z\u0100-\u017F\u1E00-\u1EFF\u00f1\u0301\u0302 —\'\-]+'
DEVA_REGEXP = r'[\u0900-\u097F\u0980-\u09FF\uA8E0-\uA8FF —\-]+'

def slp1_to_deva(input_data): 
    '''
    Return the Devanagari transliteration of the given
    data in SLP1 format
    '''
    # Drop "/", indicating udatta diacritic (cannot be transcribed with other diacritics; not in original text)
    deva_translit = transliterate(input_data.replace("/", ""), SLP1, DEVANAGARI)
    if re.fullmatch(DEVA_REGEXP, deva_translit) is None: 
        raise ValueError(f"Return value does not match regexp: {deva_translit} | {[hex(ord(c)) for c in deva_translit]}")
    return deva_translit

def slp1_to_iast(input_data): 
    '''
    Return the IAST transliteration of the given
    data in SLP1 format
    '''
    base_translit = transliterate(input_data, SLP1, IAST)
    # Use combining acute to indicate udatta accent
    full_translit = base_translit.replace("/", "\u0301")
    if re.fullmatch(IAST_REGEXP, full_translit) is None: 
        raise ValueError(f"Return value does not match regexp: {full_translit} | {[hex(ord(c)) for c in full_translit]}")
    return full_translit