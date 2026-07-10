'''
match_utils.py

A script containing helper functions for matching parsed
lemmas with lex_master lemmas.
'''
import sys, re
import termios, tty
import unicodedata

FIELDNAMES = ["src_id", "src_lemma", "src_entry", "ref_id", "ref_lemma", "ref_entry"]

def remove_accents(input_str, normalization='NFKD'): 
    normalized = unicodedata.normalize(normalization, input_str)
    return "".join(c for c in normalized if not unicodedata.combining(c))

def entry_match(parsed_entry_only, master_entry_only, *, allow_pfx_match=True):
    '''
    Return boolean dictating whether entry strings,
    having been stripped of diacritics, match, 
    subject to normalization constraints.

    allow_pfx_match: if set, returns True if `parsed_entry_only` matches 
    *at least the beginning* of master_entry_only after normalization.

    allow_sfx_match: if set, returns True if `parsed_entry_only` matches 
    master_entry_only` after normalization, excluding everything up to the
    first closing parenthesis (if present - viz. excluding initial translit.).
    *DUBIOUS AT BEST*

    parsed_entry: normalize all spaces to single space
    master_entry: strip any leading numerals
    '''
    # normalize spacing & diacritic marks
    parsed_normal = re.sub(r' +', ' ', remove_accents(parsed_entry_only))
    master_normal = re.sub(r' +', ' ', remove_accents(master_entry_only))

    match_bool = False
    if allow_pfx_match:
       match_bool = (re.match(re.escape(parsed_normal), master_normal) is not None)

    return match_bool or (parsed_normal == master_normal)

def getch():
    '''Helper function to capture a single char from terminal input'''
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)              # raw mode: no line buffering
        ch = sys.stdin.read(1)    # read one byte
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)