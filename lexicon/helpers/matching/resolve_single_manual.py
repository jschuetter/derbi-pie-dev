'''
manual_matching.py

A quick-and-dirty script for manual matching of lemmas using terminal window
'''

import os, sys, csv, time
from copy import deepcopy
from match_utils import *

input_file = 'temp/unique_matches.csv'

remaining_file_path = 'temp/unique_remaining.csv'
if os.path.exists(remaining_file_path): 
    print("Do you want to start from temp/unique_remaining.csv?")
    ch = getch()
    if ch in ("y", "\r", "\n"):
        input_file = remaining_file_path

with open(input_file, 'r') as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)


rows_remaining = deepcopy(rows)
rows_approved = []
rows_rejected = []
count = 0
sys.stdout.write("\033[?7l")
sys.stdout.flush()
no_save = False
try:
    auto_match_only = False
    for r in rows: 
        count += 1
        print("Lemma:", count)
        print(r["reflex"], "/", r["lemma"])
        print("lex_ref_link:", r["gloss_eng"])
        print("lex_master:", r["gloss"])
        print(r["entry_str"])
        print()
        print("Do these entries match?")
        # Wait for user response
        while True:
            ch = getch()
            if ch in ("y", "\r", "\n"):
                rows_approved.append(r)
                break
            elif ch in ("n", "\b", "\x7f"):
                rows_rejected.append(r)
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
        rows_remaining.remove(r)
        os.system('cls' if os.name == 'nt' else 'clear')
finally: 
    if no_save: 
        sys.exit()


    with open(remaining_file_path, 'w') as remfile: 
        writer = csv.DictWriter(remfile, FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows_remaining)
    with open(f'approved/unique_manual_{time.time()}.csv', 'w') as appfile: 
        writer = csv.DictWriter(appfile, FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows_approved)
    with open(f'rejected/unique_manual_{time.time()}.csv', 'w') as rejfile: 
        writer = csv.DictWriter(rejfile, FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows_rejected)

    print("Rows reviewed:", count)
    print("Approved:", len(rows_approved))
    print("Rejected:", len(rows_rejected))
    print("Remaining:", len(rows_remaining))
    sys.stdout.write("\033[?7h")
    sys.stdout.flush()