"""
lexdata.py
Script for running data through CLTK to get additional lexicon fields
"""

from cltk.phonology.non.phonology import OldNorseTranscription

def ipa_oldnorse(input_orth): 
    '''
    Return the IPA transcription of the given orthography
    Based on the docs at 
    https://v1.cltk.org/en/latest/cltk.phonology.non.html#cltk.phonology.non.phonology.OldNorseTranscription

    Returns empty string if transcription fails 
    (as for 'þrywja', an alternate orthography for 'þrumda')
    '''
    ont = OldNorseTranscription()
    try: 
        ipa = ont.transcribe(input_orth)
        return ipa
    except KeyError as ke: 
        print(f"Could not transcribe '{input_orth}' (KeyError: {ke})")
        return ""