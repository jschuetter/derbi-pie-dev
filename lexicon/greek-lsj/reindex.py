'''
reindex.py

A simple script designed to reindex entries from 
`grc.lsj.perseus-eng2.csv` onward to handle skipped IDs
in Perseus CSVs
==Missing IDs:==
n20214 (CSV 2)
n77575 (CSV 17)
n78758 (CSV 17)
n98366 (CSV 21)
n99905 (CSV 21)

Will unify with existing lex_master schema.
'''

import csv

for csv_num in range(21, 28): 
    filename = f'grc.lsj.perseus-eng{csv_num}.csv'
    # Read rows from CSV
    with open(filename, 'r') as readfile: 
        reader = csv.DictReader(readfile)
        rows = list(reader)
    # Iterate over rows, incrementing lemma_id as necessary
    for row in rows: 
        id = int(row["lemma_id"])
        # if id > 99905: 
        if id >= 99903: # DEV
            row["lemma_id"] = id - 1 
        # if id > 98366: 
        # if id >= 98365: # DEV
        #     row["lemma_id"] = id - 1 
        # if id > 78758: 
        #     row["lemma_id"] = id - 1 
        # if id > 77575: 
        #     row["lemma_id"] = id - 1 
        # if id > 20214:
        #      row["lemma_id"] = id - 1

    # Write back to CSV
    with open(filename, 'w') as writefile: 
        writer = csv.DictWriter(writefile, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        print("Reindexed", filename)