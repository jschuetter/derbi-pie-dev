"""
lexdata.py
Script for running data through CLTK to get additional lexicon fields
"""
from cltk.phonology.grc.phonology import GreekTranscription
from romanize import romanize

import csv
from copy import deepcopy

from lxml import etree

def ipa_greek(input_orth):
    '''
    Return the IPA transcription of the given orthography
    Based on the docs at 
    https://v1.cltk.org/en/latest/cltk.phonology.non.html#cltk.phonology.non.phonology.OldNorseTranscription

    Returns empty string if transcription fails 
    '''
    grt = GreekTranscription()
    try: 
        ipa = grt.transcribe(input_orth)
        return ipa
    except KeyError as ke: 
        print(f"Could not transcribe '{input_orth}' (KeyError: {ke})")
        return ""

def greek_to_roman(input_data):
    '''
    Return the Roman transliteration of the given Greek script
    '''
    if input_data == "":
        return ""
    
    return romanize(input_data)