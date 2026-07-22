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
    "p;",
    "pp.", #  (past participle form)
    "pp,",
    "ppr.",
    # "pp. of",
    "part.", #  (present participle)
    "part,",
    # "part. of",
    "pres. part.",
    "subj.", #  (???)
    "subj. pres.",
    "subj. indef.",
    "imp.", #  (imperative)
    "imp. s.",
    "impert.",
    # "sing. impert. of",
    "instr.",
    "indef.",
    "sub.",
    "3rd sing.",
    "pres. indic.",
    "prs.",

    # Nouns
    "gen.",
    "dat.",
    "acc.",
    "abl.",
    "g.",
    "d.",
    # "gen. dat.",  # Sometimes used to indicate a verb that takes a gen./dat. object (in entry, not in orth - remediate manually)
    "pl.",
    "pl,",
    ", pl.",
    "m;",
    "f;",
    "n;",
    "m",
    "f",
    "n",
    "indecl.",
    "indecl.:",
    "indecl. :",
    "indecl;",
    "indecl?",
    "m:",
    "f:",
    "n:",
    "dat. instr.",
    "pl. gen.",
    "nom. pl.",
    "n: pl.",
    # Random one-offs
    "pl. n. acc.", 
    "pl. nom. acc.", 
    "nom. acc. pl.", 
    "gen. dat. acc.",
    "nom. acc: gen.",
    "indecl. in sing; pl. nom. acc.",
    "indecl. in sing.; pl.",
    "indecl. in s; pl. nom. acc.",
    "indecl. in s. but sometimes gen.",
    "indecl. in sing. but gen.",
    "indecl: but Lat.",
    "m. f. n. indecl. but in dat. and inst. pl.",
    "but often indecl. in sing; pl. nom. acc.",

    # Adjectives
    "def.",
    "comp.",
    "comp. m.",
    "comp, m.",
    "cpve.",
    "cpve.:",
    "superl.",
    "sup.",
    "f. n.",
    "gen. m. n.",
    "dat. m. n.",
    "acc. m.",

    # Prepositions
    "dat;",
]

# Valid POS abbreviations
POS = [
    "v.",
    "v. trans.",
    "v.trans.",
    "v.intrans.",
    "v. a.",
    "v.a.",
    "v. n.",
    "v. reflex.",
    "v. pers. and impers.",
    "adj.",
    "adv.",
    "adv,",
    "adj. pron.",
    "spve. adj.",
    "spve. adv.",
    
    "prep.",
    "conj.",
    "pron.",
    "possess, pron.",
    "indef. prn.",
]
POS_PREP = [
    "prep. dat.",
    "prep. c. dat.",
    "prep. with dat.",
    "prep, with dat., gen.",
    "prep, with dt.",
    "prep. dat. and instr.",
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
    "m?",
    "f.",
    "f?",
    "n.",
    "n?",
    "m. n.",
    "m,",
    "f,",
    "n,",
    "indecl. m.",
    "indecl. f.",
    "indecl. n.",
    "indecl; m.",
    "indecl; f.",
    "indecl; n.",
    "m. indecl.",
    "f. indecl.",
    "n. indecl.",
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
POS_ALL = POS + POS_PREP + POS_IMPLIES_N + POS_IMPLIES_V + POS_W_GLOSS
# Abbreviations to keep in entry
POS_KEEP_IN_ENTRY = POS_PREP + POS_IMPLIES_V 
POS_REMOVE = [x for x in POS_ALL if x not in POS_KEEP_IN_ENTRY]

# Lists of abbrevs. for imputing POS (when not found in line)
# Gloss words that indicate verbs
IMPUTE_V_GLOSS = [
    "To",
    "to",
    "trans.",
    "intrans."
    "v. trans.",
    "v. intrans."
]
IMPUTE_N_GLOSS = [
    "A",
    "An",
    "The",
    "a",
    "an",
    "the",
    "indecl.",
]
IMPUTE_V_ORTH = [
    "p.", #  (preterite singular form)
    "pp.", #  (past participle form)
    "pp. of",
    "part.", #  (present participle)
    "part. of",
    "subj.", #  (???)
    "impert.", #  (imperative)
    "sing. impert. of",
]
IMPUTE_N_ORTH = [
    "gen.",
    "dat.",
    "acc.",
    "abl.",
    "m;",
    "f;",
    "n;",
    "indecl.",
    "indecl;",
    "m:",
    "f:",
    "n:",
    # Random one-offs
    "pl. n. acc.", 
    "indecl. in sing; pl. nom. acc.",
    "indecl. in s; pl. nom. acc.",
    "indecl: but Lat.",
    "m. f. n. indecl. but in dat. and inst. pl.",
    "but often indecl. in sing; pl. nom. acc.",
]

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