'''
renum_main.py

Helpers for adding indexing to parsed CSVs
'''

import csv, sys, os

def renumber_main(input): 
    '''
    Renumber main senses to match convention in
    other lexica: `sense_num` field on main/master 
    entries is used to differentiate duplicate 
    lemmas, not for display delimiters.

    Input may be file or raw data
    '''
    print("Reading input")
    output_rows = []
    if type(input) == str: 
        with open(input, 'r') as csvfile: 
            r = csv.DictReader(csvfile)
            data = list(r)
    else: 
        data = input

    matching_rows = []
    lemma_match = None
    num_main = 0
    for row in data: 
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

    return output_rows

def renumber_senses(input):
    '''
    Add sense_id and h_number to auxiliary 
    senses where missing in input data.
     
    N.B. will not detect sense hierarchy (viz.
    will leave parent_h_num blank).

    Input may be file or raw data
    '''
    print("Reading input")
    output_rows = []
    if type(input) == str: 
        with open(input, 'r') as csvfile: 
            r = csv.DictReader(csvfile)
            data = list(r)
    else: 
        data = input

    sense_idx = 1
    match_lemma_id = None
    lemma_sense_idx = 0
    for row in data: 
        if row["type"] == "sense":
            if row["lemma_id"] == match_lemma_id: 
                lemma_sense_idx += 1
            else: 
                match_lemma_id = row["lemma_id"]
                lemma_sense_idx = 0

            if "sense_id" not in row or row["sense_id"] == "\\N":
                row["sense_id"] = sense_idx
                sense_idx += 1
            if "h_number" not in row or row["h_number"] == "\\N":
                row["h_number"] = f"n{row["lemma_id"]}.{lemma_sense_idx}"

        output_rows.append(row)

    return output_rows

if __name__ == "__main__":
    from save_csv import save_csv

    if len(sys.argv) < 2 or os.path.splitext(sys.argv[1])[-1] != ".csv": 
        print("Please provide the path to an input CSV file.")
        sys.exit()

    rn_main = renumber_main(sys.argv[1])
    save_csv(rn_main, f"{os.path.splitext(sys.argv[1])[0]}-renumbered.csv")