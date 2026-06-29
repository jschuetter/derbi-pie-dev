'''
Goal: resolve all matches found using MySQL so 
that each `parsed_id` matches to exactly one 
`master_id`, *or* is assigned a new `master_id`
not yet used in `lex_master`
'''
import csv, re

# Resolving `skt_single_matches`:
## Want to eliminate transcription issues from consideration
'''
Transcription patterns: 
- Correct transcription: 'a-kāraṇôtpanna (अ-कारणो̂त्पन्न)' [ iast-iast (deva-deva) ]
- Incorrect transcription: 'a-kāraṇo (अ-कारणो)tpanna' [ iast-iast (deva-deva)slp1 ]

N.B. seems to be caused by <srs/> tag breaking up SLP1 transcription

Delimiters: 
comma + or + gender
'a-cira—rocis (अ-चिर—रोचिस्), f. or acirā̂ṃśu (अचिरा̂ंशु), m. or acirā̂bhā (अचिरा̂भा), f.   lightning.'
comma + or?
'aṅgúri (अङ्गुरि), is (इस्), or aṅgurī (अङ्गुरी) [L.],   f. (for aṅguli (अङ्गुलि), q.v.) a finger, AV.'

Possible solution: 
- Run re.findall() on bad transcription pattern in `master_entry_str`
- Run approx_match() method on found matches
- Test rest of string (excluding transliterations) for match
- If all matches return True, ID pairing is approved

1. Resolve all auto-approvable matches
2. Extract duplicates, remediate manually
3. Assign new indices to unmatched IDs
'''
import lexdata

# Modify regexp to include literal '^' and '/' (not converted to diacritics in lex_master)
modified_iast_regexp = r'(?=[A-Za-z\u0100-\u017F\u1E00-\u1EFF\u00f1\u0300-\u0302\u0306\u221a])[A-Za-z\u0100-\u017F\u1E00-\u1EFF\u00f1\u0300-\u0302\u0306\u221a\u00b0+—\'\-;\[\],!\.‘’=~?\^/]+'
modified_deva_regexp = r'(?=[\u0900-\u097F\u0980-\u09FF\uA8E0-\uA8FF\u221a])[\u0900-\u097F\u0980-\u09FF\uA8E0-\uA8FF\u221a\u00b0+—\-;\[\],!‘’=~?\^/]+'
tl_re_good = r'('+modified_iast_regexp+r'?) \(('+modified_deva_regexp+r'?)\)'
tl_re_bad = r'('+modified_iast_regexp+r'?) \(('+modified_deva_regexp+r'?)\)([a-zA-Z/\^\-\u00b0]+)?' # Transliteration with SLP1 following

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
    
def entry_match(parsed_entry_only, master_entry_only, allow_pfx_match=True):
    '''
    Return boolean dictating whether entry strings,
    having been stripped of transliterations, match, 
    subject to normalization constraints.

    allow_pfx_match: if set, returns True if `parsed_entry_only` matches 
    *at least the beginning* of master_entry_only after normalization.

    parsed_entry: normalize all spaces to single space
    master_entry: strip any leading numerals
    '''
    parsed_normal = re.sub(r' +', ' ', parsed_entry_only)
    master_normal = re.sub(r'^[0-9]+\.[ ]+?', '', master_entry_only)

    if allow_pfx_match:
       return re.match(re.escape(parsed_normal), master_normal) is not None 
    else: 
        return parsed_normal == master_normal

def fix_translit(master_match):
    '''
    Return a copy of master_entry_str with bad 
    transliteration captured in master_match 
    replaced by corrected transliteration
    '''
    un_tl = master_match.group(1)
    if master_match.group(3) is not None: 
        un_tl += '\u0302' + lexdata.slp1_to_iast(master_match.group(3))
    return f'{un_tl} ({lexdata.iast_to_deva(un_tl)})'

# TODO: handle accent-only discrepancies?
# TODO: get rid of processing aside from master_resolved??

with open('sql-matching/skt_single_matches.csv', 'r') as csv_single:
    r = csv.DictReader(csv_single)
    approved_rows = []
    unmatched_rows = []
    discrepant_rows = []
    eq_unmatched = 0
    eq_resolved = 0
    for row in r: 
        approved = False
        parsed_matches = list(re.finditer(tl_re_good, row["parsed_entry_str"]))
        master_matches = list(re.finditer(tl_re_bad, row["master_entry_str"]))

        if len(parsed_matches) > len(master_matches): 
            # More transliterations in parsed entry than master
            # => almost certainly different entries
            # => separate into different list
            discrepant_rows.append(row)
            continue

        # Create master_resolved
        row["master_resolved"] = row["master_entry_str"][:master_matches[0].span()[0]] if len(master_matches) > 0 else row["master_entry_str"]
        match_idx = 0
        while match_idx < len(parsed_matches):
            match = master_matches[match_idx]
            row["master_resolved"] += fix_translit(match)
            next_match_start = master_matches[match_idx+1].span()[0] if match_idx < len(master_matches)-1 else None
            row["master_resolved"] += row["master_entry_str"][match.span()[1]:next_match_start]
            match_idx += 1
        while match_idx < len(master_matches):
            match = master_matches[match_idx]
            un_tl = match.group(1)
            if match.group(3) is not None: 
                un_tl += '\u0302' + (match.group(3) or '')
            # Map initial character back to capital, if applicable
            for ch, sub in lexdata.un_tl_map.items():
                un_tl = re.sub(r'^'+ch, sub, un_tl)
            row["master_resolved"] += un_tl
            next_match_start = master_matches[match_idx+1].span()[0] if match_idx < len(master_matches)-1 else None
            row["master_resolved"] += row["master_entry_str"][match.span()[1]:next_match_start]
            match_idx += 1
        if entry_match(row["parsed_entry_str"], row["master_resolved"]):
            eq_resolved += 1
            approved = True
        
        # Try different matching approach - may catch some that above did not
        if not approved: 
            paired_matches = list(zip(parsed_matches, master_matches))
            tl_matches = [transliteration_match(pm, mm) for (pm, mm) in paired_matches]
            
            if all(tl_matches):
                parsed_no_tl = re.sub(tl_re_good, '', row["parsed_entry_str"])
                master_no_tl = re.sub(tl_re_bad, '', row["master_entry_str"])

                # If discrepancy in match counts, try to remediate mistaken transliterations in lex_master
                if len(parsed_matches) < len(master_matches):
                    for match in master_matches[len(parsed_matches):]:
                        # Untransliterate: reconstruct full string (if split)
                        # then convert back to original form, treating as if 
                        # converting IAST to SLP1
                        # N.B. only treat word-initial capitals => use replacement map instead?
                        un_tl = match.group(1)
                        if match.group(3) is not None: 
                            un_tl += '\u0302' + (match.group(3) or '')
                        # Map initial character back to capital, if applicable
                        for ch, sub in lexdata.un_tl_map.items():
                            un_tl = re.sub(r'^'+ch, sub, un_tl)
                        # print("Match:", match.group(0), "| un_tl:", un_tl)
                        master_no_tl = master_no_tl.replace(match.group(0), un_tl, 1)

                no_tl_match = entry_match(parsed_no_tl, master_no_tl)
                if no_tl_match: 
                    approved = True
            

        if approved:
            approved_rows.append(row)
        else:
            if len(parsed_matches) != len(master_matches): 
                eq_unmatched += 1
            unmatched_rows.append(row)

    print(len(approved_rows), "approved")
    print(eq_resolved, "from master_resolved")
    print(len(unmatched_rows), "not matched"),
    print(len(discrepant_rows), "set aside as discrepant")

with open('sql-matching/single-approved.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(approved_rows)
with open('sql-matching/single-unmatched.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(unmatched_rows)
with open('sql-matching/single-discrepant.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(discrepant_rows)
## Want to handle entries which were split into add'l senses or lemmas