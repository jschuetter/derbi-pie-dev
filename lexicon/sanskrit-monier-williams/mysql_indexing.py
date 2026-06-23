'''
mysql_indexing.py

Script for matching lemmas in monier-williams-tempidx.csv (parser output)
to lemmas in existing MySQL database, for the purpose of preserving 
`lex_master_id`s
'''

import os, re, csv, json
import mysql.connector
from time import time

PARSED_CSV_PATH = "monier-williams-tempidx.csv"
JSON_PATH_APPROVED = "mw-matches-approved.json"
JSON_PATH_REPEAT = "mw-matches-repeat-review.json"
JSON_PATH_UNIQUE = "mw-matches-unique-review.json"
JSON_PATH_MULTIPLE = "mw-matches-multiple-review.json"
JSON_PATH_UNMATCHED = "mw-matches-not-found.json"

# Search for matching lemmas in lex_master_src
# Create output table(s) for manual approval
# - matches exactly one lemma
# - multiple lemma matches
# - no matching lemmas found

# Separate lemmas where multiple parsed lemmas
# match to the same entry?

# Maintain lists of (lemma_id, lemma) pairs that
# were found, not found or multiples found in MySQL
# Will be exported to JSON format when execution finishes
paired_master_ids = []      # List of IDs in lex_master that have been paired with a parsed_id
approved_matches = []       # List of matches that were auto-approved (exactly matching lemma, entry_str, etc.)
repeat_pairings = []        # List of unique matches where multiple parsed_ids were paired with the same master_id
unique_matches = []         # List of unique matches which could not be auto-approved (likely correct, but need review)
unmatched_lemmas =  []      # List of lemmas without found pairing
multiple_match_lemmas = []  # List of lemmas which matched multiple master_ids (need manual remediation)


# Init. MySQL connection
conn = mysql.connector.connect(
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASS'),
    host=os.getenv('MYSQL_HOST'),
    database=os.getenv('MYSQL_DB')
    )
db = conn.cursor()
print("Initialized connection to MySQL db", os.getenv("MYSQL_DB"))
start_time = time()

with open(PARSED_CSV_PATH, 'r') as parser_file:
    r = csv.DictReader(parser_file, fieldnames=[
        "lemma_id",
        "lemma",
        "lemma_normalized",
        "lemma_translit",
        "sense_num",
        "page_num",
        "type",
        "orthography",
        "pos",
        "gender",
        "etymology",
        "entry",
        "entry_str",
        "components",
        "gloss",
        "related",
        "sense_id",
        "h_num",
        "parent_h_num"
    ])
    for entry in r: 
        if entry["type"] != "main": 
            continue

        # print("Lemma/pg:", entry["lemma_translit"], "/", entry["page_num"])
        lemma_query = (
            "SELECT lemma_id, lemma, entry_str FROM lex_master "
            "WHERE lemma LIKE %s "
            "AND page_num = %s"
        )
        db.execute(lemma_query, (f"{entry["lemma_translit"]} (%)", entry["page_num"]))
        lemma_matches = db.fetchall()
        # print(len(lemma_matches), "matches:", *lemma_matches)
        print(f"{entry["lemma_translit"]} / {entry["lemma_id"]} (pg. {entry["page_num"]}) : {len(lemma_matches)} matches ", end="")
        if len(lemma_matches) < 1: 
            # No match found
            unmatched_lemmas.append({
                "parsed_id": entry["lemma_id"],
                "parsed_lemma": entry["lemma_translit"],
                "parsed_entry_str": entry["entry_str"]
            })
        else:
            # One or more matches
            
            # Check for exact match
            match_found = False
            for match in lemma_matches:
                # Normalize entry_str for matching
                master_entry_str_normalized = re.sub(r'^[0-9]+\.\s?', '', match[2])
                parsed_entry_str_normalized = re.sub(r' +', ' ', entry["entry_str"])
                if (
                    entry["lemma_translit"] == match[1].split()[0] # If lemma matches exactly
                    and
                    parsed_entry_str_normalized == master_entry_str_normalized
                ):
                    print("(exact match)")
                    master_id = match[0]
                    if master_id not in paired_master_ids:
                        paired_master_ids.append(master_id)
                        approved_matches.append({
                            "parsed_id": entry["lemma_id"],
                            "master_id": match[0],
                            "parsed_lemma": entry["lemma_translit"],
                            "master_lemma": match[1],
                            "parsed_entry_str": entry["entry_str"],
                            "master_entry_str": match[2],
                            "already_matched": match[0] in paired_master_ids,
                        })

                    match_found = True
                    break

            # If exact match found, continue to next entry
            if match_found: 
                continue
            
            # Else, sort into appropriate list
            if len(lemma_matches) > 1: 
                # Multiple matches
                ids_paired = [ (row[0] in paired_master_ids) for row in lemma_matches ]
                if any(ids_paired): 
                    print("(paired)")
                else: 
                    print("(not paired)")
                multiple_match_lemmas.append({
                    "parsed_id": entry["lemma_id"],
                    "master_id": [ row[0] for row in lemma_matches ],
                    "parsed_lemma": entry["lemma_translit"],
                    "master_lemma": [ row[1] for row in lemma_matches ],
                    "parsed_entry_str": entry["entry_str"],
                    "master_entry_str": [ row[2] for row in lemma_matches ],
                    "already_matched": ids_paired
                })
            else: 
                # Single match - check ID
                master_id = lemma_matches[0][0]
                if master_id not in paired_master_ids:
                    print("(not paired)")
                    paired_master_ids.append(master_id)
                    unique_matches.append({
                        "parsed_id": entry["lemma_id"],
                        "master_id": lemma_matches[0][0],
                        "parsed_lemma": entry["lemma_translit"],
                        "master_lemma": lemma_matches[0][1],
                        "parsed_entry_str": entry["entry_str"],
                        "master_entry_str": lemma_matches[0][2],
                        "already_matched": lemma_matches[0][0] in paired_master_ids,
                    })
                else: 
                    print("(paired)")
                    repeat_pairings.append({
                        "parsed_id": entry["lemma_id"],
                        "master_id": lemma_matches[0][0],
                        "parsed_lemma": entry["lemma_translit"],
                        "master_lemma": lemma_matches[0][1],
                        "parsed_entry_str": entry["entry_str"],
                        "master_entry_str": lemma_matches[0][2],
                        "already_matched": lemma_matches[0][0] in paired_master_ids,
                    })

print("Finished pairing:", time() - start_time, "s")

# JSON syntax: 
'''
[
    {
        "parsed_id": str
        "master_id": str or list
        "parsed_lemma": str (transliterated)
        "master_lemma": str or list
        "parsed_entry_str": str
        "master_entry_str": str or list
        "already_matched": optional list (if master_id is already matched)
    }
]
'''
'''
Auto-approve matches IF: 
- exactly one match from DB
- parsed_lemma exactly matches *first word* of master_lemma
- parsed_entry_str exactly matches *start* of master_entry_str
    (N.B. must ignore stripped <hom> markings and unnormalized spaces - use re.sub?)
- master_id *not* already paired with another parsed_id
'''

# Write JSON files
with open(JSON_PATH_APPROVED, 'w') as f: 
    json.dump(approved_matches, f, indent=4)

with open(JSON_PATH_REPEAT, 'w') as f: 
    json.dump(repeat_pairings, f, indent=4)
    
with open(JSON_PATH_UNIQUE, 'w') as f: 
    json.dump(unique_matches, f, indent=4)
    
with open(JSON_PATH_MULTIPLE, 'w') as f: 
    json.dump(multiple_match_lemmas, f, indent=4)
    
with open(JSON_PATH_UNMATCHED, 'w') as f: 
    json.dump(unmatched_lemmas, f, indent=4)

db.close()
conn.close()

print("JSON files written.")
print("Execution completed.", time() - start_time, "s")