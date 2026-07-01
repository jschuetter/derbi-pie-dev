'''
Goal: resolve all matches found using MySQL so 
that each `parsed_id` matches to exactly one 
`master_id`, *or* is assigned a new `master_id`
not yet used in `lex_master`
'''
import csv, re
import pandas as pd
import matplotlib.pyplot as plt
from rapidfuzz.distance import Levenshtein

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
from match_utils import *

with open('sql-matching/skt_single_matches.csv', 'r') as csv_single:
    r = csv.DictReader(csv_single)
    approved_rows = []
    approx_match_rows = []
    unmatched_rows = []
    discrepant_rows = []

    ld_distances = []
    ld_good = []
    ld_bad = []

    eq_resolved = 0
    for row in r: 
        # Try literal string match first
        if entry_match(row["parsed_entry_str"], row["master_entry_str"]):
            approved_rows.append(row)
            continue
        
        parsed_matches = list(re.finditer(tl_re_good, row["parsed_entry_str"]))
        master_matches = list(re.finditer(tl_re_bad, row["master_entry_str"]))

        if len(parsed_matches) > len(master_matches): 
            # More transliterations in parsed entry than master
            # => almost certainly different entries
            # => separate into different list
            discrepant_rows.append(row)
            continue
        
        match_resolutions = resolve_matches(parsed_matches, master_matches)

        # Create master_resolved
        row["master_resolved"] = row["master_entry_str"][:master_matches[0].span()[0]] if len(master_matches) > 0 else row["master_entry_str"]
        match_idx = 0
        if row["parsed_lemma"] == "agnīṣomā":
            print(parsed_matches)
            print(list(zip(master_matches, match_resolutions)))
        for match_idx in range(len(master_matches)): 
            # Replace each match with appropriate resolution
            row["master_resolved"] += match_resolutions[match_idx]
            next_match_start = master_matches[match_idx+1].span()[0] if match_idx < len(master_matches)-1 else None
            row["master_resolved"] += row["master_entry_str"][master_matches[match_idx].span()[1]:next_match_start]

        if entry_match(row["parsed_entry_str"], row["master_resolved"]):
            eq_resolved += 1
            approved_rows.append(row)
            continue
        
        # Try different matching approach - may catch some that above did not
        #region tlMatch
        paired_matches = list(zip(parsed_matches, master_matches))
        tl_matches = [transliteration_match(pm, mm) for (pm, mm) in paired_matches]
        
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
                # Map initial character back to capital, if applicable (also after hyphens)
                for ch, sub in lexdata.un_tl_map.items():
                    un_tl = re.sub(r'(?:^|-)'+ch, sub, un_tl)
                # print("Match:", match.group(0), "| un_tl:", un_tl)
                master_no_tl = master_no_tl.replace(match.group(0), un_tl, 1)

        no_tl_match = entry_match(parsed_no_tl, master_no_tl)
        if no_tl_match and all(tl_matches): 
            approved_rows.append(row)
            continue
        elif no_tl_match:
            approx_match_rows.append(row)
            continue
        #endregion
        
        # Calculate similarity distance of row for metrics
        ld = Levenshtein.normalized_similarity(row["parsed_entry_str"], row["master_resolved"]) * 100
        ld_distances.append(ld)
        if ld > 85: 
            ld_good.append(row|{"levenshtein":ld})
            approved_rows.append(row)
        else: 
            ld_bad.append(row|{"levenshtein":ld})
            unmatched_rows.append(row)


    print(len(approved_rows), "approved")
    print(eq_resolved, "from master_resolved")
    print(len(approx_match_rows), "approx. matches")
    print(len(unmatched_rows), "not matched"),
    print(len(discrepant_rows), "set aside as discrepant")

with open('sql-matching/single-approved.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(approved_rows)
with open('sql-matching/single-approx.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(approx_match_rows)
with open('sql-matching/single-unmatched.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(unmatched_rows)
with open('sql-matching/single-discrepant.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(discrepant_rows)
with open('sql-matching/single-ld-good.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['levenshtein','parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(ld_good)
with open('sql-matching/single-ld-bad.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, ['levenshtein','parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
    writer.writeheader()
    writer.writerows(ld_bad)

df_counts = pd.Series(ld_distances).value_counts(bins=100).sort_index()
df_counts.to_csv('ld_distances.csv')
plt.figure()
plt.bar(df_counts.index.astype(str), df_counts.values)
plt.xlabel('Value ranges')
plt.ylabel('Count')
plt.savefig('LD-distances-plot.png')