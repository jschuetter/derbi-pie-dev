"""
lexdata.py
Script for running data through CLTK to get additional lexicon fields
"""

from cltk.phonology.ang.phonology import OldEnglishTranscription

def ipa_oldenglish(input_orth): 
    '''
    Return the IPA transcription of the given orthography
    Based on the docs at 
    https://v1.cltk.org/en/latest/cltk.phonology.non.html#cltk.phonology.non.phonology.OldNorseTranscription

    Returns empty string if transcription fails 
    (as for 'þrywja', an alternate orthography for 'þrumda')
    '''
    oet = OldEnglishTranscription()
    try: 
        ipa = oet.transcribe(input_orth)
        return ipa
    except KeyError as ke: 
        print(f"Could not transcribe '{input_orth}' (KeyError: {ke})")
        return ""