'''
resolve_multiple_auto.py

Script for automatically matching lex_ref_link entries which
matched multiple lemmas in lex_master.

Approach: 
- Check Levenshtein distance with each 'ref_entry' string.
    - If any found > 85, auto-approve
    - If one found in (60,85], or multiple > 60, mark for manual approval
    - If none found > 50, discard for new indexing
'''

import csv, sys, os
from rapidfuzz.distance import Levenshtein
from match_utils import *

if not len(sys.argv) > 1: 
    print("Please provide the path of a CSV to process")
    sys.exit()

with open(sys.argv[1], 'r') as csv_multiple:
    r = csv.DictReader(csv_multiple, fieldnames=["src_id", "src_lemma", "src_entry", "ref_id", "ref_lemma", "ref_entry"])
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
            first_row_id = first_row["src_id"]
            id_matches = [first_row]
            next_row = next(r)
            next_row.update({"levenshtein":-1})
            # Collect all matches for src_id
            while next_row["src_id"] == first_row_id:
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
                if entry_match(row["src_entry"], row["ref_entry"]):
                    match_approved[-1] = 101
                    continue

                # Calculate similarity distance of row for metrics
                ld = Levenshtein.normalized_similarity(row["src_entry"], row["ref_entry"]) * 100
                row.update({"levenshtein":ld})
                id_matches[len(match_approved)-1].update({"levenshtein":ld})
                match_approved[-1] = ld
            
            # Process matches
            # If any match has Levenshtein over 85, auto-approve highest
            # (throw out other rows)
            max_ld = max(match_approved)
            if max_ld > 90:
                idx_max = match_approved.index(max_ld)
                max_match = id_matches[idx_max]
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
        print(review_count, "set aside for review")
        print(unmatched_count, "not matched"),

        if not os.path.exists('./output'): 
            os.makedirs('output')
        with open('output/multiple-approved.csv', 'w') as appfile:
            writer = csv.DictWriter(appfile, ['levenshtein', 'src_id', 'ref_id', 'src_lemma', 'ref_lemma', 'src_entry', 'ref_entry'])
            writer.writeheader()
            writer.writerows(approved_matches)
        with open('output/multiple-review.csv', 'w') as appfile:
            writer = csv.DictWriter(appfile, ['levenshtein','src_id', 'ref_id', 'src_lemma', 'ref_lemma', 'src_entry', 'ref_entry'])
            writer.writeheader()
            writer.writerows(review_matches)
        with open('output/multiple-unmatched.csv', 'w') as appfile:
            writer = csv.DictWriter(appfile, ['levenshtein','src_id', 'ref_id', 'src_lemma', 'ref_lemma', 'src_entry', 'ref_entry'])
            writer.writeheader()
            writer.writerows(unmatched_rows)