"""
lexdata.py
Script for retrieving additional lexical information
N.B. CLTK lacks a Sanskrit IPA transcription module
(e.g. phonetic transcription, transliteration, etc.)
"""

from indic_transliteration.sanscript import transliterate, SLP1, IAST, DEVANAGARI

def slp1_to_deva(input_data): 
    '''
    Return the Devanagari transliteration of the given
    data in SLP1 format
    '''
    return transliterate(input_data, SLP1, DEVANAGARI)

def slp1_to_iast(input_data): 
    '''
    Return the IAST transliteration of the given
    data in SLP1 format
    '''
    return transliterate(input_data, SLP1, IAST)