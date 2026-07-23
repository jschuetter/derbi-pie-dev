'''
resolve_multiple_manual.py

Like resolve_single_manual.py, but for parsed lemmas
that matched several in lex_master

Asks user to approve matches for a given lemma in order of 
likeliness (determined by normalized Levenshtein distance).
Once a user approves a match for a given lemma, remaining 
options for that lemma (parsed_id) will be dropped.
'''

import os, sys, csv, time

from match_utils import *

input_file = 'oe_duplicate_matches.csv'

remaining_file_path = 'oe_multiple_remaining.csv'
if os.path.exists(remaining_file_path): 
    print("Do you want to start from oe_multiple_remaining.csv?")
    ch = getch()
    if ch in ("y", "\r", "\n"):
        input_file = remaining_file_path

with open(input_file, 'r') as infile:
    reader = csv.DictReader(infile)

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
            first_row_id = first_row["lex_ref_link_id"]
            next_row = next(reader)
            # Consume all rows with matching parsed_id
            id_matches = [first_row]
            while next_row["lex_ref_link_id"] == first_row_id:
                id_matches.append(next_row)
                next_row = next(reader)

            option = 0
            match_found = False
            for row in id_matches: 
                no_match = False
                print("Lemma:", count)
                option += 1
                print(first_row_id, "option:", option, "/", len(id_matches))
                print("lex_ref_link:", row["gloss_eng"])
                print("lex_master:", row["gloss"])
                print(row["entry_str"])
                print("Do these entries match?")
                print("\n\n\n\n")
                print("Other entries:")
                for m in id_matches[option:]:
                    print(m["entry_str"])
                # Wait for user response
                while True:
                    ch = getch()
                    # Row matches; approve and drop all other options
                    if ch in ("y", "\r", "\n"):
                        approved_matches.append(row)
                        match_found = True
                        break
                    # Row does not match; continue to other options
                    elif ch in ("n", "\b", "\x7f"):
                        break
                    elif ch in ("\x03", "\x1b"):
                        print("Do you want to save your changes?")
                        confirm = getch()
                        if confirm in ("y", "\r", "\n"):
                            raise KeyboardInterrupt
                        elif confirm in ("n", "\b", "\x7f"):
                            no_save = True
                            raise KeyboardInterrupt
                        else: 
                            print("Cancelling...")
                os.system('cls' if os.name == 'nt' else 'clear')
                if match_found: 
                    break
            if not match_found: 
                unmatched_rows.extend(id_matches)
    except KeyboardInterrupt: 
        pass
    except StopIteration: 
        pass
    finally: 
        if no_save: 
            sys.exit()

        # Consume remaining rows
        rows_remaining = []
        try: 
            if row: 
                rows_remaining.append(row)
            while True: 
                rows_remaining.append(next(reader))
        except StopIteration: 
            with open(remaining_file_path, 'w') as remfile: 
                writer = csv.DictWriter(remfile, FIELDNAMES)
                writer.writeheader()
                writer.writerows(rows_remaining)

        with open(f'multiple_manual_approved_{time.time()}.csv', 'w') as appfile: 
            writer = csv.DictWriter(appfile, FIELDNAMES)
            writer.writeheader()
            writer.writerows(approved_matches)
        with open(f'multiple_manual_unmatched_{time.time()}.csv', 'w') as rejfile: 
            writer = csv.DictWriter(rejfile, FIELDNAMES)
            writer.writeheader()
            writer.writerows(unmatched_rows)

        print("Rows reviewed:", count)
        print("Approved:", len(approved_matches))
        print("Rejected:", count-len(approved_matches))
        print("Remaining:", len(rows_remaining))
        sys.stdout.write("\033[?7h")
        sys.stdout.flush()