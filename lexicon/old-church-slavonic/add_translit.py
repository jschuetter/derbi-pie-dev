'''
add_translit.py

A script for sorting original orth & 
transliteration into appropriate fields to
match established convention. 

`lemma`: original script
`lemma_normalized`: original script, stripped of accents/diacritics
`lemma_translit`: Roman transliteration of lemma
`orthography`: original script of lemma, including any hyphens,
plus other forms of the word
'''

import csv

print("Reading input")
output_rows = []
with open("old-church-slavonic.csv", 'r') as csvfile: 
    r = csv.DictReader(csvfile)
    for row in r: 
        row["lemma_normalized"] = row["lemma"]
        row["lemma_translit"] = row["orthography"]  # Orthography field currently holds Roman transliteration
        row["orthography"] = row["lemma"]
        output_rows.append(row)

print("Writing output")
with open("old-church-slavonic.csv", 'w') as outfile: 
    w = csv.DictWriter(outfile, output_rows[0].keys())
    w.writeheader()
    w.writerows(output_rows)