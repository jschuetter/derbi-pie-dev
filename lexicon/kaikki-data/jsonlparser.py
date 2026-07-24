'''
jsonlparser.py

A simple parser script for processing the JSONL
file downloaded from Kaikki to filter out the 
desired entries (those pertaining to Old Church Slavonic)

Input: raw Wiktextract JSONL data from Kaikki
    (path stored in RAW_FILE)
  
Output: JSONL (JSON Lines) file containing only OCS entries
    (path stored in OUTPUT_FILE)
    WARNING: will overwrite any previous output at the same location
'''

RAW_FILE = "raw-wiktextract-data.jsonl"
OUTPUT_FILE = "ocs-lexicon.jsonl"

from time import time

def parse_jsonl(input_file=RAW_FILE, output_file=None, *, lang, lang_code):
    ocs_entries = []
    if output_file is None: 
        output_file = f"{lang_code}-lexicon.jsonl"
    #region WIKTEXTRACT SNIPPET
    # Code taken from documentation at: 
    # https://github.com/tatuylonen/wiktextract#pre-extracted-data
    import json

    with open(input_file, encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
    #endregion
            if "lang" not in data: 
                # Redirect entries do not have all metadata present
                # print(data)
                continue
            elif data["lang"] == lang or data["lang_code"] == lang_code:
                    ocs_entries.append(data)

    # Output selected lines into 
    with open(output_file, "w") as of: 
        for line in ocs_entries: 
            of.write(json.dumps(line) + "\n")

if __name__ == "__main__": 
    import sys
    if len(sys.argv) < 3: 
        print("Please provide a `lang` and `lang_code` to search for in the Wiktextract data.")
        sys.exit()
    
    print(f"Searching for lang='{sys.argv[1]}' or lang_code='{sys.argv[2]}'...")
    start_time = time()
    parse_jsonl(lang=sys.argv[1], lang_code=sys.argv[2])
    print("Data extract completed. Runtime:", time() - start_time, "s")