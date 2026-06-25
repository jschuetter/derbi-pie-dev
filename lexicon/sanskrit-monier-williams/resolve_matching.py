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

tl_re_good = r'('+lexdata.IAST_REGEXP+r') \(('+lexdata.DEVA_REGEXP+r')\)'
tl_re_bad = r'('+lexdata.IAST_REGEXP+r') \(('+lexdata.DEVA_REGEXP+r')\)([a-zA-Z/^]+)?' # Transliteration with SLP1 following

def transliteration_match(parsed_match, master_match): 
    '''
    Return boolean dictating whether (correct) transcription parsed
    matches (mangled) transcription from lex_master

    Arguments: two re.Match objects
    Requirements: prefix match + tail match
    '''
    # if re.match(re.escape(master_match.group(1)), parsed_match.group(0)) is not None: 
    #     print("Prefix match")

    if '\u0302' in parsed_match.group(1):
        # Transcription broken
        match_re = re.escape(master_match.group(1) + '\u0302' + lexdata.slp1_to_iast((master_match.group(3) or '')))
        return re.match(match_re, parsed_match.group(0)) is not None
    else: 
        # Transcription should be normal
        return re.match(re.escape(master_match.group(0)), parsed_match.group(0)) is not None
    
def entry_match(parsed_entry_only, master_entry_only):
    '''
    Return boolean dictating whether entry strings,
    having been stripped of transliterations, match, 
    subject to normalization constraings

    parsed_entry: normalize all spaces to single space
    master_entry: strip any leading numerals
    '''
    parsed_normal = re.sub(r' +', ' ', parsed_entry_only)
    master_normal = re.sub(r'^[0-9]+\.[ ]+?', '', master_entry_only)

    return parsed_normal == master_normal

with open('sql-matching/skt_single_matches.csv', 'r') as csv_single:
    r = csv.DictReader(csv_single)
    approved_rows = []
    unmatched_rows = []
    for row in r: 
        parsed_matches = re.finditer(tl_re_good, row["parsed_entry_str"])
        master_matches = re.finditer(tl_re_bad, row["master_entry_str"])
        paired_matches = list(zip(parsed_matches, master_matches))
        tl_matches = [transliteration_match(pm, mm) for (pm, mm) in paired_matches]

        parsed_no_tl = re.sub(tl_re_good, '', row["parsed_entry_str"])
        master_no_tl = re.sub(tl_re_bad, '', row["master_entry_str"])
        no_tl_match = entry_match(parsed_no_tl, master_no_tl)
        # print(all(tl_matches), no_tl_match)
        if tl_matches and no_tl_match:
            approved_rows.append(row)
        else:
            unmatched_rows.append(row)

    print(len(approved_rows), "approved")
    print(len(unmatched_rows), "not matched")

with open('sql-matching/single-approved.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(approved_rows)
with open('sql-matching/single-unmatched.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(unmatched_rows)
## Want to handle entries which were split into add'l senses or lemmas