'''
resolve_multiple_manual.py

Like resolve_single_manual.py, but for reflexes
that matched several in lex_master

Asks user to approve matches for a given lemma in order of 
likeliness (determined by normalized Levenshtein distance).
Once a user approves a match for a given lemma, remaining 
options for that lemma (src_id) will be dropped.
'''

import os, sys, csv, time, re

from match_utils import getch

IGNORE_LESSER = False  # Ignore match options with a greater Levenshtein distance than first

if not os.path.exists('./output'): 
    os.makedirs('output')

input_file = None
remaining_file_path = 'output/multiple-manual-remaining.csv'
if os.path.exists(remaining_file_path): 
    print("Do you want to start from multiple-manual-remaining.csv?")
    ch = getch()
    if ch in ("y", "\r", "\n"):
        input_file = remaining_file_path
if not input_file: 
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]): 
        input_file = sys.argv[1]
    else: 
        print("Please provide the path of a CSV to process")
        sys.exit()

FIELDNAMES = ["src_id", "src_lemma", "src_entry", "ref_id", "ref_lemma", "ref_entry"]

with open(input_file, 'r', newline='') as infile:
    reader = csv.DictReader(infile, fieldnames=FIELDNAMES)

    approved_matches = []
    unmatched_rows = []
    count = 0
    # Prevent text wrapping in terminal
    sys.stdout.write("\033[?7l")
    sys.stdout.flush()
    no_save = False
    try:
        next_row = next(reader)
        while True: # Loop until all rows in DictReader consumed
            count += 1
            first_row = next_row
            first_row_id = first_row["src_id"]
            next_row = next(reader)
            # Consume all rows with matching src_id
            id_matches = [first_row]
            while next_row["src_id"] == first_row_id:
                id_matches.append(next_row)
                next_row = next(reader)

            option = 0
            match_found = False
            print("Lemma:", count)
            option += 1
            print("option:", option, "/", len(id_matches))
            print(first_row["src_lemma"], "/", first_row["ref_lemma"])
            print("\n", first_row["src_entry"], "\n")
            rownum = 0
            for row in id_matches:
                rownum += 1
                print(rownum, "-", row["ref_entry"])
            # Wait for user response
            while True:
                res = input("Which definition matches best?\n")
                # Row matches; approve and drop all other options
                if re.match(r'[0-9]+', res): 
                    res_int = int(res)
                    if res_int == 0:
                        # No match found
                        break
                    if res_int > len(id_matches): 
                        print("Option unavailable")
                        continue
                    approved_matches.append(id_matches[res_int-1])
                    match_found = True
                    break
                # Row does not match; continue to other options
                elif res in ("n", "N", "no", "No", "none", "None"):
                    break
                else: 
                    # Invalid response
                    continue
            os.system('cls' if os.name == 'nt' else 'clear')
            if not match_found: 
                unmatched_rows.extend(id_matches)
    except KeyboardInterrupt: 
        print("Do you want to save your changes?")
        confirm = getch()
        if confirm in ("y", "\r", "\n"):
            pass
        elif confirm in ("n", "\b", "\x7f"):
            no_save = True
    except StopIteration: 
        pass
    finally: 
        if no_save: 
            sys.exit()

        # Consume remaining rows
        rows_remaining = []
        try: 
            while True: 
                rows_remaining.append(next(reader))
        except StopIteration: 
            with open(remaining_file_path, 'w') as remfile: 
                writer = csv.DictWriter(remfile, FIELDNAMES)
                writer.writeheader()
                writer.writerows(rows_remaining)

        with open(f'output/multiple-manual-approved-{time.time()}.csv', 'w') as appfile: 
            writer = csv.DictWriter(appfile, FIELDNAMES)
            writer.writeheader()
            writer.writerows(approved_matches)
        with open(f'output/multiple-manual-unmatched-{time.time()}.csv', 'w') as rejfile: 
            writer = csv.DictWriter(rejfile, FIELDNAMES)
            writer.writeheader()
            writer.writerows(unmatched_rows)

        print("Rows reviewed:", count)
        print("Approved:", len(approved_matches))
        print("Rejected:", count-len(approved_matches))
        print("Remaining:", len(rows_remaining))