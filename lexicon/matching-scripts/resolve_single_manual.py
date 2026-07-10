'''
manual_matching.py

A quick-and-dirty script for manual matching of lemmas using terminal window
'''

import os, sys, csv, termios, tty, time, re
from match_utils import *

input_file = None

if not os.path.exists('./output'): 
    os.makedirs('output')

input_file = None
remaining_file_path = 'output/single-manual-remaining.csv'
if os.path.exists(remaining_file_path): 
    print("Do you want to start from single-manual-remaining.csv?")
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

approved_matches = []
unmatched_rows = []
with open(input_file, 'r', newline='') as infile:
    reader = csv.DictReader(infile)
    sys.stdout.write("\033[?7l")
    sys.stdout.flush()
    no_save = False
    count = 0
    try:
        for r in reader: 
            rows_remaining = [r]
            count += 1
            print("Lemma:", count)
            print()
            print(r["src_lemma"], "/", r["ref_lemma"], "\n")
            print("Src:", r["src_entry"])
            print("Ref:", r["ref_entry"])
            print("\nDo these entries match?")
            # Wait for user response
            while True:
                ch = getch()
                if ch in ("y", "\r", "\n"):
                    approved_matches.append(r)
                    break
                elif ch in ("n", "\b", "\x7f"):
                    unmatched_rows.append(r)
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
    except KeyboardInterrupt: 
        pass
    except StopIteration:
        pass
    finally: 
        if no_save: 
            sys.exit()

        # Consume remaining rows
        try: 
            while True: 
                rows_remaining.append(next(reader))
        except StopIteration: 
            with open(remaining_file_path, 'w') as remfile: 
                writer = csv.DictWriter(remfile, FIELDNAMES)
                writer.writeheader()
                writer.writerows(rows_remaining)

        with open(f'output/single-manual-approved-{time.time()}.csv', 'w') as appfile: 
            writer = csv.DictWriter(appfile, FIELDNAMES)
            writer.writeheader()
            writer.writerows(approved_matches)
        with open(f'output/single-manual-rejected-{time.time()}.csv', 'w') as rejfile: 
            writer = csv.DictWriter(rejfile, FIELDNAMES)
            writer.writeheader()
            writer.writerows(unmatched_rows)

        print("Rows reviewed:", count)
        print("Approved:", len(approved_matches))
        print("Rejected:", len(unmatched_rows))
        print("Remaining:", len(rows_remaining))