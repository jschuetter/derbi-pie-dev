'''
match_utils.py

A script containing helper functions for matching parsed
lemmas with lex_master lemmas.
'''
import sys, re
import termios, tty
import lexdata

# Modify regexp to include literal '^' and '/' (not converted to diacritics in lex_master)
# IAST, plus punctuation (must begin with IAST character)
modified_iast_regexp = r'(?=[A-Za-z\u0100-\u017F\u1E00-\u1EFF\u00f1\u0300-\u0302\u0306\u221a])[A-Za-z\u0100-\u017F\u1E00-\u1EFF\u00f1\u0300-\u0302\u0306\u221a\u00b0+—\'\-;\[\],!\.‘’=~?\^/]+?'
# Deva characters, plus punctuation, plus untransliterated IAST (must include Deva characters somewhere in match)
modified_deva_regexp = r'(?=[\S]*[\u0900-\u097F\u0980-\u09FF\uA8E0-\uA8FF\u221a])[\u0900-\u097F\u0980-\u09FF\uA8E0-\uA8FF\u221a\u00b0+—\-;\[\],!‘’=~?\^/\u0100-\u017F\u1E00-\u1EFF\u00f1a-zA-Z]+?'
tl_re_good = r'('+modified_iast_regexp+r') \(('+modified_deva_regexp+r')\)'
tl_re_bad = r'('+modified_iast_regexp+r') \(('+modified_deva_regexp+r')\)([a-zA-Z/\^\-\u00b0]+)?( \('+modified_deva_regexp+r'\))?' # Transliteration with SLP1 following

def transliteration_match(parsed_match, master_match): 
    '''
    Return boolean dictating whether (correct) transcription parsed
    matches (mangled) transcription from lex_master

    Arguments: two re.Match objects
    Requirements: prefix match + tail match
    '''
    # if re.match(re.escape(master_match.group(1)), parsed_match.group(0)) is not None: 
    #     print("Prefix match")

    if master_match.group(3) is not None:
        # Transcription broken
        match_re = re.escape(master_match.group(1) + '\u0302' + lexdata.slp1_to_iast(master_match.group(3)))
        return re.match(match_re, parsed_match.group(0)) is not None
    else: 
        # Transcription should be normal
        return re.match(re.escape(master_match.group(0)), parsed_match.group(0)) is not None
    
def entry_match(parsed_entry_only, master_entry_only, *, allow_pfx_match=True, allow_sfx_match=False):
    '''
    Return boolean dictating whether entry strings,
    having been stripped of transliterations, match, 
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
    parsed_normal = re.sub(r' +', ' ', parsed_entry_only)
    if re.match(r'[0-9]', master_entry_only) and not re.match(r'[0-9]', parsed_entry_only):
        master_normal = re.sub(r'^[0-9]+\.[ ]+?', '', master_entry_only)
    else: 
        master_normal = master_entry_only

    # Ignore combining circumflex, acute, grave
    parsed_normal = re.sub(r'[\u0300-\u0302]', '', parsed_normal)
    master_normal = re.sub(r'[\u0300-\u0302]', '', master_normal)

    match_bool = False
    if allow_pfx_match:
       match_bool = (re.match(re.escape(parsed_normal), master_normal) is not None)
    if not match_bool and allow_sfx_match: 
        parsed_suffix_begin = [m.end() for m in re.finditer(lexdata.DEVA_REGEXP+r'\)\s*', parsed_normal)]
        if parsed_suffix_begin:
            parsed_suffix = parsed_normal[parsed_suffix_begin[0]:]
            if master_normal.rfind(parsed_suffix) != -1 and len(parsed_suffix.split()) > 2: 
                # If suffixes match, auto-approve and print
                match_bool = True

    return match_bool or (parsed_normal == master_normal)

def fix_translit(master_match):
    '''
    Return a copy of master_entry_str with bad 
    transliteration captured in master_match 
    replaced by corrected transliteration
    '''
    un_tl = master_match.group(1)
    if master_match.group(3) is not None: 
        un_tl += '\u0302' + lexdata.slp1_to_iast(master_match.group(3))
    # Replace '^' with combining grave
    return f'{un_tl.replace("^", "\u0300")} ({lexdata.iast_to_deva(un_tl)})'

def match_accent_insensitive(str1, str2):
    '''
    Returns boolean string equality value, 
    ignoring combining acute, grave, and circumflex 
    '''
    return re.sub(r'[\u0300-\u0302]', '', str1) == re.sub(r'[\u0300-\u0302]', '', str2)

def resolve_matches(parsed_matches, master_matches):
    '''
    Return a list of substitutions for each match in master_matches.
    
    For matches also found in parsed_matches: fix transliteration.
    For matches not found in parsed_matches: undo transliteration.
    '''
    resolutions = []
    for match in master_matches: 
        match_fixed = fix_translit(match)
        if any(match_accent_insensitive(match_fixed, pm.group(0)) for pm in parsed_matches):
            resolutions.append(match_fixed)
        else: 
            un_tl = match.group(1)
            if match.group(3) is not None: 
                un_tl += '\u0302' + (match.group(3) or '')
            # Map initial character back to capital, if applicable
            for ch, sub in lexdata.un_tl_map.items():
                un_tl = re.sub(r'(^|-)'+ch, r'\1'+sub, un_tl)
            resolutions.append(un_tl)

    return resolutions

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