'''
jsonlreader.py
Reader script for `lithuanian-lexicon.jsonl` to convert
Wiktextract JSON format to DERBi PIE CSV database schema
'''

import json, csv
from time import time

SQL_NULL = "\\N"

def get_entries(filename): 
    '''
    Return a dict of entries from the provided
    JSONL file
    '''

    # Load lexicon entries from JSONL file
    jsonl_entries = []
    with open(filename, "r") as f: 
        for line in f: 
            jsonl_entries.append(json.loads(line))
    
    dict_entries = []
    lemma_idx = 1 # Start indexing at 1 to match SQL convention
    for ent in jsonl_entries: 
        lemma = ent["word"]
        pos = ent["pos"] if "pos" in ent else ""
        gender = ""
        if pos in ["noun", "name"]:
            try: 
                main_form_tags = ent["forms"][0]["tags"]
                if not main_form_tags[0] == "canonical": 
                    raise ValueError("Not canonical form")
                if main_form_tags[1] not in ["masculine", "feminine", "neuter"]: 
                    raise ValueError("No valid gender found")
                else: 
                    gender = main_form_tags[1]
            except KeyError: 
                # Forms or tags field not found
                pass
            except ValueError: 
                # Appropriate value not found where expected
                pass
        
        orth = ""
        try: 
            orth = ent["forms"][0]["form"]
        except KeyError: 
            # Forms field or entry not found
            pass
            
        ipa = ""
        try: 
            ipa = ent["sounds"]["ipa"]
        except KeyError: 
            # Leave IPA field blank if not listed
            pass

        entry_str = ""
        if "raw_glosses" in ent["senses"][0]:
            entry_str = "; ".join(ent["senses"][0]["raw_glosses"])
        else: 
            entry_str = "; ".join(ent["senses"][0]["glosses"])

        # Wrap entry_str in HTML
        entry = f'<div class="lithuanian bodytext">{entry_str}</div>'
        
        # Construct entry object
        # N.B. no page num., stem, or components information
        new_entry = {
            "lemma_id": lemma_idx,
            "lemma": lemma,
            "sense_num": "",
            "type": "main",
            "orthography": orth,
            "ipa": ipa,
            "pos": pos,
            "gender": gender,
            "etymology": ent["etymology_text"],
            "entry": entry,
            "entry_str": entry_str,
            "gloss": ent["senses"][0]["glosses"][0]
        }
        new_entries = [new_entry]

        if len(ent["senses"]) > 0: 
            new_entry["sense_num"] = "[1]"
            # Iterate over remaining senses
            for sense_idx in range(1,len(ent["senses"])):
                sense = ent["senses"][sense_idx]
                sense_entry_str = ""
                if "raw_glosses" in sense: 
                    sense_entry_str = "; ".join(sense["raw_glosses"])
                else: 
                    sense_entry_str = "; ".join(sense["glosses"])
                # Wrap sense_entry_str in HTML
                sense_entry = f'<div class="lithuanian bodytext">{sense_entry_str}</div>'

                new_sense = {
                    "lemma_id": lemma_idx,
                    "lemma": lemma,
                    "sense_num": f"[{sense_idx+1}]",
                    "type": "sense",
                    "orthography": "",
                    "ipa": "",
                    "pos": "",
                    "gender": "",
                    "etymology": "",
                    "entry": sense_entry,
                    "entry_str": sense_entry_str,
                    "gloss": sense["glosses"][0]
                }
                new_entries.append(new_sense)

        for ne in new_entries: 
            for k,v in ne.items():
                # Convert empty fields to SQL_NULL
                if v == "":
                    ne[k] = SQL_NULL
            dict_entries.append(ne)

    return dict_entries

def save_csv(data, filename):
    fieldnames = ["lemma_id", "lemma", "sense_num", "type", "orthography", "ipa", "pos", "gender", "etymology", "entry", "entry_str", "gloss"]
    rows = [{
        "lemma_id": ent["lemma_id"],
        "lemma": ent["lemma"], 
        "sense_num": ent["sense_num"],
        "type": ent["type"],
        "orthography": ent["orthography"],
        "ipa": ent["ipa"], 
        "pos": ent["pos"],
        "gender": ent["gender"],
        "etymology": ent["etymology"],
        "entry": ent["entry"],
        "entry_str": ent["entry_str"],
        "gloss": ent["gloss"]
        } for ent in data]
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(rows)  # Write data rows

if __name__ == "__main__":
    start_time = time()
    entries = get_entries("lithuanian-lexicon.jsonl")
    save_csv(entries, "lithuanian.csv")
    print("Parsing completed.")
    print("Runtime:", time() - start_time, "s")