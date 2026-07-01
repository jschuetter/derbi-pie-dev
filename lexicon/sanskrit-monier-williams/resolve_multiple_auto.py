'''
resolve_multiple_auto.py

Script for automatically matching parsed lemmas which
matched multiple lemmas in lex_master.

Approach: 
- Check Levenshtein distance with each 'master_resolved' string.
    - If any found > 85, auto-approve
    - If one found in (60,85], or multiple > 60, mark for manual approval
    - If none found > 50, discard for new indexing
'''

import csv, re
from rapidfuzz.distance import Levenshtein
from match_utils import *

with open('sql-matching/skt_multiple_matches.csv', 'r') as csv_multiple:
    r = csv.DictReader(csv_multiple)
    approved_matches = []
    duplicate_approved_matches = []
    review_matches = []
    review_count = 0
    unmatched_rows = []
    unmatched_count = 0
    
    try: 
        next_row = next(r)
        next_row.update({"levenshtein":-1})
        while True:  # Loop until all items have been read
            first_row = next_row
            first_row_id = first_row["parsed_id"]
            id_matches = [first_row]
            next_row = next(r)
            next_row.update({"levenshtein":-1})
            # Collect all matches for parsed_id
            while next_row["parsed_id"] == first_row_id:
                id_matches.append(next_row)
                next_row = next(r)
                next_row.update({"levenshtein":-1})
            
            # Test all matches
            # Make list of "match" values -- either equal to normalized Levenshtein dist.,
            # or = 100 for exact match, or = -1 if outright discrepant.
            match_approved = []
            for row in id_matches: 
                # Instantiate approval value
                match_approved.append(0)

                # Try literal string match first
                if entry_match(row["parsed_entry_str"], row["master_entry_str"]):
                    match_approved[-1] = 101
                    continue
                
                parsed_matches = list(re.finditer(tl_re_good, row["parsed_entry_str"]))
                master_matches = list(re.finditer(tl_re_bad, row["master_entry_str"]))

                if len(parsed_matches) > len(master_matches): 
                    # Match rejected
                    match_approved[-1] = -1
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
                    match_approved[-1] = 102
                    continue
                
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
                if no_tl_match:
                    match_approved[-1] = 103
                    continue
                
                # Calculate similarity distance of row for metrics
                ld = Levenshtein.normalized_similarity(row["parsed_entry_str"], row["master_resolved"]) * 100
                row.update({"levenshtein":ld})
                id_matches[len(match_approved)-1].update({"levenshtein":ld})
                match_approved[-1] = ld
            
            # Process matches
            # If any match has Levenshtein over 85, auto-approve highest
            # (throw out other rows)
            max_ld = max(match_approved)
            if max_ld > 85:
                idx_max = match_approved.index(max_ld)
                max_match = id_matches[idx_max]
                if int(max_match["master_lemma_paired"]) == 1: 
                    max_match.update({"levenshtein":max_ld})
                    duplicate_approved_matches.append(max_match)
                else: 
                    approved_matches.append(max_match)
                continue
            # If any match has Levenshtein over 60, set aside for review
            elif max_ld > 60: 
                review_count += 1
                review_matches.extend(sorted(id_matches, key=lambda r : r["levenshtein"], reverse=True))
                continue
            # Otherwise, assume no match present
            else: 
                unmatched_count += 1
                unmatched_rows.extend(id_matches)
                continue


    except StopIteration: 
        print(len(approved_matches), "matches found")
        print(len(duplicate_approved_matches), "already-assigned matches found")
        print(review_count, "set aside for review")
        print(unmatched_count, "not matched"),

        with open('sql-matching/multiple-approved.csv', 'w') as appfile:
            writer = csv.DictWriter(appfile, ['levenshtein', 'parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str', 'master_lemma_paired'])
            writer.writeheader()
            writer.writerows(approved_matches)
        with open('sql-matching/multiple-approved-duplicates.csv', 'w') as appfile:
            writer = csv.DictWriter(appfile, ['levenshtein', 'parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str', 'master_lemma_paired'])
            writer.writeheader()
            writer.writerows(duplicate_approved_matches)
        with open('sql-matching/multiple-review.csv', 'w') as appfile:
            writer = csv.DictWriter(appfile, ['levenshtein','parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str', 'master_lemma_paired'])
            writer.writeheader()
            writer.writerows(review_matches)
        with open('sql-matching/multiple-unmatched.csv', 'w') as appfile:
            writer = csv.DictWriter(appfile, ['levenshtein','parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str', 'master_lemma_paired'])
            writer.writeheader()
            writer.writerows(unmatched_rows)