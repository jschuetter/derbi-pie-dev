"""
lexdata.py
Script for running data through CLTK to get additional lexicon fields
"""

from cltk.phonology.ang.phonology import OldEnglishTranscription

# Abbreviations used in orthography notation
ORTH = [
    # Verbs
    "pl.", #  (plural present ending)
    "p.", #  (preterite singular form)
    "pp.", #  (past participle form)
    "pp. of",
    "part.", #  (present participle)
    "part. of",
    "subj.", #  (???)
    "impert.", #  (imperative)
    "sing. impert. of",

    # Nouns
    "gen.",
    "dat.",
    "acc.",
    "abl.",
    "pl.",
    "pl. n. acc.", # For some reason
]

# Valid POS abbreviations
POS = [
    "v. trans.",
    "v. intrans.",
    "v. a.",
    "v. n.",
    "v. reflex.",
    "v. pers. and impers.",
    "adj.",
    "adv.",
    "adj. pron.",
    
    # Prepositions
    "prep.",
    "prep. dat.",
    "prep. c. dat.",
    "prep. with dat.",
    "prep. cum dat. inst. acc.",
    "prep. with dat. acc. inst.",
    "prep. acc.",
]
# POS abbreviations which imply v.
POS_IMPLIES_V = [
    "trans.",
    "intrans."
]
# Gender abbreviations (imply n.)
POS_IMPLIES_N = [
    "m.",
    "f.",
    "n.",
    "m. n.",
]
# Only valid when gloss included with POS abbrev. in <I>
# cf. 'Ingwine', 'Indéas'
POS_W_GLOSS = [
    # Number/Gender - imply n.
    "pl.",
    "pl. f.",
    "pl. m.",
    "pl. n.",
]
POS_ALL = POS + POS_IMPLIES_N + POS_IMPLIES_V + POS_W_GLOSS

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