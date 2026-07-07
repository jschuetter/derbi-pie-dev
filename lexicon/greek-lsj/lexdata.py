"""
lexdata.py
Script for running data through CLTK to get additional lexicon fields
"""
from cltk.phonology.grc.phonology import GreekTranscription
from cltk.tag.pos import POSTag
from romanize import romanize

# Install Greek NLP models from Github, if not already
from cltk.utils import CLTK_DATA_DIR
import os
models_path = os.path.join(CLTK_DATA_DIR, "grc/model/")
if not os.path.exists(models_path):
    # Clone grc_models_cltk repo
    print("Importing 'grc_models_cltk' from GitHub")
    from cltk.data.fetch import FetchCorpus
    fc = FetchCorpus("grc")
    fc.import_corpus("grc_models_cltk")
    print("Installed 'grc_models_cltk' in cltk_data directory")

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

def pos_greek(input_word): 
    '''
    Returns POS abbrev. of input word 
    (expects single word)

    Mapping:
    N: noun
    V: verb
    A: adjective
    D: adverb
    R: preposition
    C: conjunction (also G?)
    M: numeral
    T: participle
    I: interjection (also E for exclamation?)
    P: pronoun
    '''
    ABBREV_MAP = {
        "N": "n.",
        "V": "v.",
        "A": "adj.",
        "D": "adv.",
        "R": "prep.",
        "C": "conj.",
        "G": "conj.",
        "M": "numer.",
        "T": "part.",
        "I": "interj.",
        "E": "interj.",
        "P": "pron.",
    }

    try: 
        tagger = POSTag('grc')
        tagged = tagger.tag_unigram(input_word)
        if tagged[0][1] is None: 
            if len(tagged) > 1 and tagged[1][1] is not None: 
                pos_val = tagged[1][1][0]
                if pos_val != "-": 
                    return ABBREV_MAP[pos_val]
            # No tag returned
            return None
            
        pos_val = tagged[0][1][0]
        if pos_val == "-": 
            return None
        else:
            return ABBREV_MAP[pos_val]
    except KeyError as ke: 
        # Return None if unexpected value returned
        print(f"WARN: unexpected POS key {ke} for lemma {input_word}")
        return None

def greek_to_roman(input_data):
    '''
    Return the Roman transliteration of the given Greek script
    '''
    if input_data == "":
        return ""
    
    return romanize(input_data)