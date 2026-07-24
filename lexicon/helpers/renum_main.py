'''
renum_main.py

Script for renumbering main senses to match
convention in other lexica: `sense_num` field 
on main/master entries is used to differentiate
duplicate lemmas, not for display delimiters.
'''

import csv, sys, os

def renumber_main(input_file): 
    print("Reading input")
    output_rows = []
    with open(input_file, 'r') as csvfile: 
        r = csv.DictReader(csvfile)
        matching_rows = []
        lemma_match = None
        num_main = 0
        for row in r: 
            assert len(row.keys()) == len(r.fieldnames), f"{len(row.keys())}/{len(r.fieldnames)} - {row}"
            if lemma_match is None:
                # No lemma to be matched (viz. init)
                assert matching_rows == []
                lemma_match = row["lemma"]
                matching_rows.append(row)
                assert row["type"] != "sense"
                num_main += 1
                continue
            elif row["lemma"] == lemma_match:
                # Row matching test lemma
                matching_rows.append(row)
                if row["type"] != "sense":
                    num_main += 1
                continue
            else: 
                # Row does not match
                assert len(matching_rows) > 0
                if num_main > 1: 
                    # More than one matching main entry;
                    # Do renumbering
                    match_idx = 1
                    for m in matching_rows: 
                        if m["type"] != "sense":
                            m["sense_num"] = match_idx
                            match_idx += 1
                        output_rows.append(m)

                else: 
                    # No renumbering to do - set 'main' entry to Null
                    for m in matching_rows:
                        if m["type"] != "sense":
                            m["sense_num"] = "\\N"
                        output_rows.append(m)

                assert row["type"] != "sense"
                matching_rows = [ row ]
                lemma_match = row["lemma"]
                num_main = 1

    print("Writing output")
    output_path = f"{os.path.splitext(input_file)[0]}-renumbered.csv"
    with open(output_path, 'w') as outfile: 
        w = csv.DictWriter(outfile, fieldnames=output_rows[0].keys())
        w.writeheader()
        w.writerows(output_rows)

if __name__ == "__main__":
    if len(sys.argv) < 2 or os.path.splitext(sys.argv[1])[-1] != ".csv": 
        print("Please provide the path to an input CSV file.")
        sys.exit()

    renumber_main(sys.argv[1])