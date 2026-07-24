'''
split_matches.py

A script for dividing unique/duplicate matches from MySQL literal match output.
See `MySQL/oldenglish/matchReflexesOE.sql`
'''

import csv, sys
from match_utils import FIELDNAMES

unique_matches = []
duplicate_matches = []

if len(sys.argv) < 2: 
    input_file = input("Please provide the path to the CSV input file:\t")
else: 
    input_file = sys.argv[1]
print("Processing input file")
with open(input_file, 'r') as csvfile:
    r = csv.DictReader(csvfile, fieldnames=FIELDNAMES, escapechar="\\")
    matching_rows = []
    match_id = None
    for row in r:
        assert len(row.keys()) == 7, row
        # re-escape Null chars
        for k,v in row.items():
            if v == "N":
                row[k] = "\\N"

        if match_id is None: 
            match_id = row["lex_ref_link_id"]
            matching_rows.append(row)
            continue
        elif row["lex_ref_link_id"] == match_id:
            matching_rows.append(row)
            continue
        else: 
            # lex_ref_link_id != match_id
            if len(matching_rows) > 1: 
                duplicate_matches.extend(matching_rows)
            else: 
                assert len(matching_rows) == 1
                unique_matches.extend(matching_rows)

            # Reset with new lex_ref_link_id
            match_id = row["lex_ref_link_id"]
            matching_rows = [ row ]

# Write output files
print("Writing output files")
with open("temp/unique_matches.csv", 'w') as unique_file:
    w = csv.DictWriter(unique_file, fieldnames=FIELDNAMES)
    w.writeheader()
    w.writerows(unique_matches)

with open("temp/duplicate_matches.csv", 'w') as dup_file:
    w = csv.DictWriter(dup_file, fieldnames=FIELDNAMES)
    w.writeheader()
    w.writerows(duplicate_matches)

print("Wrote output to /temp/")