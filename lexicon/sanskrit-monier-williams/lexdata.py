"""
lexdata.py
Script for retrieving additional lexical information
N.B. CLTK lacks a Sanskrit IPA transcription module
(e.g. phonetic transcription, transliteration, etc.)
"""

import re
from indic_transliteration.sanscript import transliterate, SLP1, IAST, DEVANAGARI

# Regexp, also including U+221A (√), space, hyphen, dash, combining accents
IAST_REGEXP = r'[A-Za-z\u0100-\u017F\u1E00-\u1EFF\u00f1\u0300-\u0302\u0306\u221a\u00b0 +—\'\-;()\[\],!\.‘’=~?]+'
DEVA_REGEXP = r'[\u0900-\u097F\u0980-\u09FF\uA8E0-\uA8FF\u221a\u00b0 +—\-;()\[\],!‘’=~?]+'

def slp1_to_deva(input_data): 
    '''
    Return the Devanagari transliteration of the given
    data in SLP1 format
    '''
    if input_data == "":
        return ""
    
    # Drop "/" and "^" (accent transcriptions)
    # and circumflex accent (<srs/>)
    deva_translit = transliterate(re.sub(r'[/\^\u0302]', '', input_data), SLP1, DEVANAGARI)
    # if re.fullmatch(DEVA_REGEXP, deva_translit) is None: 
    #     print(f"Return value does not match regexp: {deva_translit} | {[hex(ord(c)) for c in deva_translit]}")
    return deva_translit

def slp1_to_iast(input_data): 
    '''
    Return the IAST transliteration of the given
    data in SLP1 format
    '''
    if input_data == "":
        return ""
    
    base_translit = transliterate(input_data, SLP1, IAST)
    # Use combining acute to indicate udatta accent,
    # Transcribe '^' as grave accent
    full_translit = base_translit.replace("/", "\u0301")
    full_translit = full_translit.replace("^", "\u0300")
    full_translit = full_translit.replace("|", ".")
    # if re.fullmatch(IAST_REGEXP, full_translit) is None: 
    #     print(f"Return value does not match regexp: {full_translit} | {[hex(ord(c)) for c in full_translit]}")
    return full_translit

def iast_to_deva(input_data):
    '''
    Return the Devanagari transliteration of the given
    data in IAST format
    '''
    if input_data == "":
        return ""
    
    # Drop "/" and "^" (accent transcriptions)
    # and circumflex accent (<srs/>)
    deva_translit = transliterate(re.sub(r'[/\^\u0302]', '', input_data), IAST, DEVANAGARI)
    # if re.fullmatch(DEVA_REGEXP, deva_translit) is None: 
    #     print(f"Return value does not match regexp: {deva_translit} | {[hex(ord(c)) for c in deva_translit]}")
    return re.sub(r'[\u1cd0-\u1cdf]', '', deva_translit) # Remove chanting accents in output

un_tl_map = {
    'ā': 'A',
    'bh': 'B', 
    'ch': 'C',
    'dh': 'D',
    'ai': 'E',
    'ṝ': 'F',
    'gh': 'G',
    'ḥ': 'H',
    'ī': 'I',
    'jh': 'J',
    'kh': 'K',
    'ḷ': 'L',
    'ṃ': 'M',
    'ṅ': 'N',
    'au': 'O',
    'ph': 'P',
    'ḍh': 'Q',
    'ṇ': 'R',
    'ś': 'S',
    'th': 'T',
    'ū': 'U',
    'V': 'V',
    'ṭh': 'W',
    'ḹ': 'X',
    'ñ': 'Y',
}