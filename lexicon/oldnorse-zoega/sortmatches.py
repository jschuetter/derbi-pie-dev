'''
sortmatches.py
A Python script to sort duplicate matches between
lex_master and lex_ref_link identified by MySQL
(dumb string match)
'''

import csv

# Read CSV
with open("oldnorse_matches.csv", 'r') as csvfile:
    fieldnames = [
        "lang",
        "lex_ref_link_id","reflex","reflex_normalized",
        "lemma_id","lemma","lemma_normalized"
    ]
    r = csv.DictReader(csvfile, fieldnames=fieldnames)
    distinct_ids = []
    single_ids = []
    duplicate_ids = []
    for row in r: 
        id = row["lex_ref_link_id"]
        if id not in distinct_ids:
            distinct_ids.append(id)
            single_ids.append(id)
        else: 
            duplicate_ids.append(id)
            try:
                single_ids.remove(id)
            except ValueError:
                pass

    # Iterate again, writing to separate files
    csvfile.seek(0)
    with open("unique_matches.csv", "w") as unique_file:
        unique_writer = csv.DictWriter(unique_file, fieldnames=fieldnames)
        unique_writer.writeheader()
        with open("duplicate_matches.csv", "w") as duplicate_file:
            duplicate_writer = csv.DictWriter(duplicate_file, fieldnames=fieldnames)
            duplicate_writer.writeheader()
            for row in r:
                id = row["lex_ref_link_id"]
                if id in single_ids:
                    unique_writer.writerow(row)
                elif id in duplicate_ids: 
                     duplicate_writer.writerow(row)
                else: 
                    raise ValueError(f"Unknown id: {id}\nRow:{row}")
    
# Make list of lex_ref_link_ids
# Remove duplicate ids
# Make separate CSVs of matches