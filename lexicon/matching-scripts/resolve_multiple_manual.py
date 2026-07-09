'''
resolve_multiple_manual.py

Like resolve_single_manual.py, but for reflexes
that matched several in lex_master

Asks user to approve matches for a given lemma in order of 
likeliness (determined by normalized Levenshtein distance).
Once a user approves a match for a given lemma, remaining 
options for that lemma (src_id) will be dropped.
'''

import os, sys, csv, time

from match_utils import getch

IGNORE_LESSER = False  # Ignore match options with a greater Levenshtein distance than first

if not os.path.exists('./output'): 
    os.makedirs('output')

remaining_file_path = 'output/multiple-manual-remaining.csv'
if os.path.exists(remaining_file_path): 
    print("Do you want to start from multiple-manual-remaining.csv?")
    ch = getch()
    if ch in ("y", "\r", "\n"):
        input_file = remaining_file_path
elif len(sys.argv) > 1 and os.path.exists(sys.argv[1]): 
    input_file = sys.argv[1]
else: 
    print("Please provide the path of a CSV to process")
    sys.exit()


with open(input_file, 'r') as infile:
    reader = csv.DictReader(infile, fieldnames=["src_id", "src_lemma", "src_entry", "ref_id", "ref_lemma", "ref_entry"])

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
            first_row_id = first_row["ref_id"]
            next_row = next(reader)
            # Consume all rows with matching src_id
            id_matches = [first_row]
            while next_row["ref_id"] == first_row_id:
                id_matches.append(next_row)
                next_row = next(reader)

            option = 0
            match_found = False
            for row in id_matches: 
                no_match = False
                print("Lemma:", count)
                option += 1
                print(first_row_id, "option:", option, "/", len(id_matches))
                print(row["levenshtein"], "LD")
                print("Source:", row["src_entry"])
                print("Ref:", row["ref_entry"])
                print("Do these entries match?")
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
                if match_found or IGNORE_LESSER: 
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
            while True: 
                rows_remaining.append(next(reader))
        except StopIteration: 
            with open(remaining_file_path, 'w') as remfile: 
                writer = csv.DictWriter(remfile, ['levenshtein','src_id', 'ref_id', 'src_lemma', 'ref_lemma', 'src_entry', 'ref_entry'])
                writer.writeheader()
                writer.writerows(rows_remaining)

        with open(f'output/multiple-manual-approved-{time.time()}.csv', 'w') as appfile: 
            writer = csv.DictWriter(appfile, ['levenshtein','src_id', 'ref_id', 'src_lemma', 'ref_lemma', 'src_entry', 'ref_entry'])
            writer.writeheader()
            writer.writerows(approved_matches)
        with open(f'output/multiple-manual-unmatched-{time.time()}.csv', 'w') as rejfile: 
            writer = csv.DictWriter(rejfile, ['levenshtein','src_id', 'ref_id', 'src_lemma', 'ref_lemma', 'src_entry', 'ref_entry'])
            writer.writeheader()
            writer.writerows(unmatched_rows)

        print("Rows reviewed:", count)
        print("Approved:", len(approved_matches))
        print("Rejected:", count-len(approved_matches))
        print("Remaining:", len(rows_remaining))