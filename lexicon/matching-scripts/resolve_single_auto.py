'''
Goal: resolve all matches found using MySQL so 
that each `parsed_id` matches to exactly one 
`master_id`, *or* is assigned a new `master_id`
not yet used in `lex_master`
'''
import os, csv, re
from rapidfuzz.distance import Levenshtein
from match_utils import *

if not os.path.exists('./output'): 
    os.makedirs('output')

if len(sys.argv) > 1 and os.path.exists(sys.argv[1]): 
    input_file = sys.argv[1]
else: 
    print("Please provide the path of a CSV to process")
    sys.exit()

with open(input_file, 'r', newline='') as infile:
    r = csv.DictReader(infile, fieldnames=FIELDNAMES)
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
        if entry_match(row["src_entry"], row["ref_entry"]):
            approved_rows.append(row)
            continue
        
        # Calculate similarity distance of row for metrics
        ld = Levenshtein.normalized_similarity(row["src_entry"], row["ref_entry"]) * 100
        ld_distances.append(ld)
        if ld > 90: 
            approved_rows.append(row)
        else: 
            unmatched_rows.append(row)


    print(len(approved_rows), "approved")
    print(len(unmatched_rows), "not matched"),

with open('output/single-approved.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, FIELDNAMES)
    writer.writeheader()
    writer.writerows(approved_rows)
with open('output/single-unmatched.csv', 'w') as appfile:
    writer = csv.DictWriter(appfile, FIELDNAMES)
    writer.writeheader()
    writer.writerows(unmatched_rows)