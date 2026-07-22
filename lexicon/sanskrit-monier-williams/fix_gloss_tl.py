'''
fix_gloss_tl.py

A quick script to fix untransliterated SLP1 in gloss field
in CSVs
'''

import csv, re
from lexdata import *
from match_utils import modified_deva_regexp, modified_iast_regexp

output_rows = []
print("Reading original file")
with open("sql-matching/skt_reindexed_main-bad_gloss.csv", 'r') as csvfile:
    r = csv.DictReader(csvfile, escapechar="\\")
    for row in r: 
        # main CSV should have 23 keys; senses 13
        assert len(row.keys()) in (23, 13), f"{row["lemma_translit"] if "lemma_translit" in row else row["lemma"]} has {len(row.keys())} keys."

        # Capture all transliterations in entry_str
        tl_list = re.findall(r'('+modified_iast_regexp+r') \(('+modified_deva_regexp+r')\)', row["entry_str"])
        # print("Original gloss:", row["gloss"])
        for tl in tl_list: 
            tl_iast = tl[0]
            tl_slp1 = iast_to_slp1(tl_iast)
            # print(tl, tl_slp1)
            row["gloss"] = re.sub(tl_slp1, tl_iast, row["gloss"])
        # Strip any stray XML tags
        row["gloss"] = re.sub(r'<span class="[a-z0-9]+?">|</span>', '', row["gloss"])
        row["gloss"] = re.sub(r'&amp;', '&', row["gloss"])
        row["entry_str"] = re.sub(r'&amp;', '&', row["entry_str"])
        # print("New gloss:", row["gloss"])
        # Fix now-unescaped null fields
        for k,v in row.items():
            if v == "N": 
                row[k] = "\\N"
        output_rows.append(row)

print("Writing output file")
with open("sql-matching/skt_reindexed_main.csv", 'w') as outfile: 
    w = csv.DictWriter(outfile, fieldnames=output_rows[0].keys())
    w.writeheader()
    w.writerows(output_rows)