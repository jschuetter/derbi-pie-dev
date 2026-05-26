"""
xmlReader.py
XML parser script for Zoega's Old Norse lexicon
"""

from lxml import etree
import csv, re
from time import time

DICT_PATH = "./zoega.xml"
SQL_NULL = "\\N"


parser = etree.XMLParser(load_dtd=True, no_network=False)
tree = etree.parse(DICT_PATH, parser=parser)
root = tree.getroot()

# Zoega dictionary XML does not include the following fields: 
# page_num, orthography, components, stem, etymology

# Lang code, editor, updated date fields will be filled in when
# importing to MySQL

lemma_idx = 1 # Start indexing at 1 to match SQL convention
for xml_entry in root.findall(".//entry"): 
    # print(xml_entry.get("word"))
    try:
        # print("Entry:", entry)
        lemma = xml_entry.get("word")
        new_entry = {
            "lemma_id": str(lemma_idx),
            "lemma": lemma,
            "sense_num": [],
            "type": "",
            "ipa": "",
            "pos": "",
            "gender": "",
            "entry": "",
            "entry_str": "",  # Plaintext of entry (without HTML tags)
            "gloss": "",
        }

        # Split entry if multiple definitions
        # Def'n delimited by `<m1><b>I)</b></m1>` 
        # (followed by 'II)', 'III)', etc.)

        # List of definitions
        # Each element contains list of tags belonging to that definition
        defn_delimiters = xml_entry.findall('.//m1[b]')
        # Print all lemmas & delimiters
        # print(lemma, *["".join(delim.itertext()) for delim in defn_delimiters])
        # DEV: make sure all delim matches contain delimiter text
        # (can't use contains() filter in lxml findall() method)
        for delim in defn_delimiters: 
            assert "I)" in "".join(delim.find("./b").itertext())
            
        # Use delimiters to split definitions
        entry_definitions = []
        if len(defn_delimiters) <= 1: 
            # If 1 delimiter or less, process entire entry as one definition
            entry_definitions.append(list(xml_entry))
        else: 
            # Multiple definitions
            defn_idx = 0
            while defn_idx < len(defn_delimiters)-1: 
                prev_idx = xml_entry.index(defn_delimiters[defn_idx])
                next_idx = xml_entry.index(defn_delimiters[defn_idx+1])
                entry_definitions.append(
                    xml_entry[prev_idx:next_idx]
                )
                defn_idx += 1
            # Append last definition
            entry_definitions.append(
                xml_entry[xml_entry.index(defn_delimiters[defn_idx]):]
            )
            print(lemma, "\n===")
            print(*["\n".join("".join(elem.itertext()) for elem in defn) for defn in entry_definitions], sep="\n---\n")
            print()


        # TODO: GET TYPE

        # Get POS or gender, as applicable
        # Select first <p> tag in entry
        p_tag = xml_entry.find(".//p")
        if p_tag in ["m.", "f.", "n."]: 
            new_entry["gender"] = p_tag
            new_entry["pos"] = "n."
        elif p_tag == "a.": 
            # Normalize 'a.' notation to 'adj.'
            new_entry["pos"] = "adj."
        else: 
            # Other tags: adj., adv., pp., prep., interj.
            new_entry["pos"] = p_tag

        # Get entry contents
        # Default case: one sense only
        # Case 1: multiple senses
        # Case 2: multiple definitions
            # Def'n delimited by `<m1><b>I)</b></m1>`
        # Case 3: multiple definitions + multiple senses


        
    except Exception as e: 
        # lemma = xml_entry.get("entry")
        print(f"Exception in entry {lemma}: {e}")