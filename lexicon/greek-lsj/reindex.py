'''
reindex.py

A simple script designed to reindex entries from 
`grc.lsj.perseus-eng2.csv` onward to handle skipped
ID at n20213 (skips n20214) -- will unify with 
existing lex_master schema
'''

import csv

for csv_num in range(2, 28): 
    filename = f'grc.lsj.perseus-eng{csv_num}.csv'
    # Read rows from CSV
    with open(filename, 'r') as readfile: 
        reader = csv.DictReader(readfile)
        rows = list(reader)
    # Iterate over rows, incrementing lemma_id as necessary
    for row in rows: 
        id = int(row["lemma_id"])
        if id > 20214: 
            row["lemma_id"] = id - 1

    # Write back to CSV
    with open(filename, 'w') as writefile: 
        writer = csv.DictWriter(writefile, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        print("Reindexed", filename)