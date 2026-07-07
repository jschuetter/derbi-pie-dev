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
    '''
    tagger = POSTag('grc')
    tagged = tagger.tag_unigram(input_word)
    if tagged[0][1] is None: 
        if len(tagged) > 1 and tagged[1][1] is not None: 
            pos_val = tagged[1][1][0]
            if pos_val != "-": 
                print(tagged)
                return pos_val
        # No tag returned
        return None
        
    pos_val = tagged[0][1][0]
    if pos_val == "-": 
        return None
    else:
        print(tagged)
        return pos_val

def greek_to_roman(input_data):
    '''
    Return the Roman transliteration of the given Greek script
    '''
    if input_data == "":
        return ""
    
    return romanize(input_data)