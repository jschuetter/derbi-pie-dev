'''
manual_matching.py

A quick-and-dirty script for manual matching of lemmas using terminal window
'''

import os, sys, csv, termios, tty, time, re

def getch():
    '''Helper function to capture a single char from terminal input'''
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)              # raw mode: no line buffering
        ch = sys.stdin.read(1)    # read one byte
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

input_file = 'sql-matching/manual-match-input.csv'

remaining_file_path = 'sql-matching/manual-match-remaining.csv'
if os.path.exists(remaining_file_path): 
    print("Do you want to start from manual-match-remaining.csv?")
    ch = getch()
    if ch in ("y", "\r", "\n"):
        input_file = remaining_file_path

with open(input_file, 'r') as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)

# Sort data
rows_sorted = sorted(rows, key=lambda r : float(r["levenshtein"]), reverse=True)

rows_remaining = rows_sorted
rows_approved = []
rows_rejected = []
count = 0
sys.stdout.write("\033[?7l")
sys.stdout.flush()
no_save = False
try:
    for r in rows_sorted: 
        # Try to auto-match using suffix, if possible
        # Ignore transliteration in parsed entry
        parsed_suffix_begin = [m.end() for m in re.finditer(r'\)\s*', r["parsed_entry_str"])]
        parsed_suffix = r["parsed_entry_str"][parsed_suffix_begin[0]:]
        if r["master_resolved"].rfind(parsed_suffix) != -1 and len(parsed_suffix.split()) > 1: 
            # If suffixes match, auto-approve and print
            print("Auto-approved lemma", r["parsed_lemma"])
            print(r["parsed_entry_str"])
            print(r["master_resolved"])
            rows_approved.append(r)
            rows_remaining.remove(r)
            continue

        count += 1
        print("Lemma:", count)
        print(r["levenshtein"], "LD")
        print("Parsed:", r["parsed_entry_str"])
        print("Master:", r["master_resolved"])
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
        writer = csv.DictWriter(remfile, ['levenshtein','parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
        writer.writeheader()
        writer.writerows(rows_remaining)
    with open(f'sql-matching/manual-approved-{time.time()}.csv', 'w') as appfile: 
        writer = csv.DictWriter(appfile, ['levenshtein','parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
        writer.writeheader()
        writer.writerows(rows_approved)
    with open(f'sql-matching/manual-rejected-{time.time()}.csv', 'w') as rejfile: 
        writer = csv.DictWriter(rejfile, ['levenshtein','parsed_id', 'master_id', 'parsed_lemma', 'master_lemma_trim', 'parsed_entry_str', 'master_resolved', 'master_entry_str'])
        writer.writeheader()
        writer.writerows(rows_rejected)

    print("Rows reviewed:", count)
    print("Approved:", len(rows_approved))
    print("Rejected:", len(rows_rejected))
    print("Remaining:", len(rows_remaining))