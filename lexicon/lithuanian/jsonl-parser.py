'''
jsonl-parser.py
A simple parser script for processing the JSONL
file downloaded from Kaikki to filter out the 
desired entries (those pertaining to Lithuanian)

Input: raw Wiktextract JSONL data from Kaikki
  (path stored in RAW_FILE)
  
Output: JSONL (JSON Lines) file containing only Lithuanian entries
  (path stored in OUTPUT_FILE)
  WARNING: will overwrite any previous output at the same location
'''

RAW_FILE = "raw-wiktextract-data.jsonl"
OUTPUT_FILE = "lithuanian-lexicon.jsonl"

from time import time

def parse_jsonl(input_file=RAW_FILE, output_file=OUTPUT_FILE):
    lithuanian_entries = []
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
            elif data["lang"] == "Lithuanian" or data["lang_code"] == "lt":
                    lithuanian_entries.append(data)

    # Output selected lines into 
    with open(output_file, "w") as of: 
        for line in lithuanian_entries: 
            of.write(json.dumps(line) + "\n")

if __name__ == "__main__": 
    start_time = time()
    parse_jsonl()
    print("Data extract completed. Runtime:", time() - start_time, "s")