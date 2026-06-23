'''
mysql_indexing.py

Script for matching lemmas in monier-williams-tempidx.csv (parser output)
to lemmas in existing MySQL database, for the purpose of preserving 
`lex_master_id`s
'''

import csv

LEX_MASTER_PATH = "lex_master_skt.csv"
PARSED_CSV_PATH = "monier-williams-tempidx.csv"

src_entries = []
parsed_entries = []
with open(LEX_MASTER_PATH, 'r') as master_file:
    r = csv.DictReader(master_file, fieldnames=[
        "lemma_id",
        "lang",
        "lemma",
        "lemma_normalized",
        "lemma_translit",
        "sense_num",
        "page_num",
        "type",
        "orthography",
        "ipa",
        "pos",
        "gender",
        "stem",
        "etymology",
        "etymology_resolved",
        "entry",
        "entry_str",
        "last_updated",
        "editor",
        "components",
        "gloss",
        "entry_type"
    ])
    for row in r: 
        src_entries.append(row)

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
    for row in r: 
        parsed_entries.append(row)

# Search for matching lemmas in lex_master_src
# Create output table(s) for manual approval
# - matches exactly one lemma
# - multiple lemma matches
# - no matching lemmas found

# Once approved, then update parsed .csv