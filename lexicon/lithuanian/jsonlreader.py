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
    sense_idx = 1 
    for ent in jsonl_entries: 
        lemma = ent["word"]
        
        orth = ""
        try: 
            orth = ent["forms"][0]["form"]
        except KeyError: 
            # Forms field or entry not found
            pass
            
        ipa = ""
        try: 
            ipa = ent["sounds"][0]["ipa"]
        except KeyError: 
            # Leave IPA field blank if not found
            pass

        pos = ent["pos"] if "pos" in ent else ""
        # Normalize forms
        if pos in ["noun", "name", "character"]: 
            pos = "n."
        elif pos == "verb": 
            pos = "v."
        elif pos == "pron": 
            pos = "pron."
        elif pos == "prep": 
            pos = "prep."
        elif pos == "intj": 
            pos = "interj."
        elif pos == "conj": 
            pos = "conj."
        elif pos == "adv": 
            pos = "adv."
        elif pos == "adj": 
            pos = "adj."
        elif pos == "prep": 
            pos = "prep."

        gender = ""
        if pos == "n.":
            try: 
                main_form_tags = ent["forms"][0]["tags"]
                if not main_form_tags[0] == "canonical": 
                    raise ValueError("Not canonical form")
                if (
                    len(main_form_tags) < 2 or 
                    main_form_tags[1] not in ["masculine", "feminine", "neuter"]
                ): 
                    raise ValueError("No valid gender found")
                else: 
                    # Normalize forms
                    if main_form_tags[1] == "masculine":
                        gender = "m."
                    elif main_form_tags[1] == "feminine": 
                        gender = "f."
                    elif main_form_tags[1] == "neuter": 
                        gender = "n."
                    else: 
                        raise Exception("This shouldn't be able to happen -- unrecognized gender")
            except KeyError: 
                # Forms or tags field not found
                pass
            except ValueError: 
                # Appropriate value not found where expected
                pass

        etym = ent["etymology_text"] if "etymology_text" in ent else ""
        etym = etym.replace("\n", "\\n")  # Escape newlines
        
        gloss = ""
        entry_str = ""
        try:
            if "raw_glosses" in ent["senses"][0]:
                entry_str = "; ".join(ent["senses"][0]["raw_glosses"])
            else: 
                entry_str = "; ".join(ent["senses"][0]["glosses"])
            gloss = ent["senses"][0]["glosses"][0]
        except KeyError as ke: 
            if (
                "tags" in ent["senses"][0] and 
                ("no-gloss" in ent["senses"][0]["tags"] or
                "empty-gloss" in ent["senses"][0]["tags"])
            ):
                print("No gloss for lemma", lemma)
            else: 
                print(lemma)
                print("Senses:", ent["senses"])
                raise ke

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
            "etymology": etym,
            "entry": f'<div class="lithuanian bodytext">{entry_str}</div>',   # Wrap entry_str in HTML
            "entry_str": entry_str,
            "gloss": gloss,
            "sense_id": "",
            "h_num": "",
            "parent_h_num": ""
        }
        new_entries = [new_entry]

        if len(ent["senses"]) > 1: 
            new_entry["sense_num"] = "1"
            # Iterate over remaining senses
            for sense_idx in range(1,len(ent["senses"])):
                sense = ent["senses"][sense_idx]

                sense_gloss = ""
                sense_entry_str = ""
                try:
                    if "raw_glosses" in sense: 
                        sense_entry_str = "; ".join(sense["raw_glosses"])
                    else: 
                        sense_entry_str = "; ".join(sense["glosses"])
                    sense_gloss = sense["glosses"][0]
                except KeyError as ke: 
                    if (
                        "tags" in sense and 
                        ("no-gloss" in sense["tags"] or
                        "empty-gloss" in sense["tags"])
                    ):
                        print(f"No gloss for lemma {lemma}, sense no. {sense_idx+1}")
                    else: 
                        print(f"{lemma}, sense_idx+1: {sense_idx+1}")
                        print("Sense:", sense)
                        raise ke

                new_sense = {
                    "lemma_id": lemma_idx,
                    "lemma": lemma,
                    "sense_num": str(sense_idx+1),
                    "type": "sense",
                    "orthography": "",
                    "ipa": "",
                    "pos": "",
                    "gender": "",
                    "etymology": "",
                    "entry": f'<div class="lithuanian bodytext">{sense_entry_str}</div>',  # Wrap sense_entry_str in HTML
                    "entry_str": sense_entry_str,
                    "gloss": sense_gloss,
                    "sense_id": sense_idx,
                    "h_num": f"n{lemma_idx}.{len(new_entries)-1}",
                    "parent_h_num": parent_ids[-1],
                }
                new_entries.append(new_sense)

        for ne in new_entries: 
            for k,v in ne.items():
                # Convert empty fields to SQL_NULL
                if v == "":
                    ne[k] = SQL_NULL
            dict_entries.append(ne)
        
        lemma_idx += 1

    return dict_entries

def save_csv(data, filename):
    fieldnames = ["lemma_id", "lemma", "sense_num", "type", "orthography", "ipa", "pos", "gender", "etymology", "entry", "entry_str", "gloss", "sense_id", "h_num", "parent_h_num"]
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
        "gloss": ent["gloss"],
        "sense_id": ent["sense_id"],
        "h_num": ent["h_num"],
        "parent_h_num": ent["parent_h_num"]
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