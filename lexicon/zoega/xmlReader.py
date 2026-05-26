"""
xmlReader.py
XML parser script for Zoega's Old Norse lexicon
"""

from lxml import etree
import csv, re
from time import time

from lexdata import *

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
        # Remove hyphens from lemma (if present) for transcription
        ipa = ipa_oldnorse(lemma.replace("-", ""))
        # print(lemma, ipa)

        # Split entry if multiple definitions
        # Def'n delimited by `<m1><b>I)</b></m1>` 
        # (followed by 'II)', 'III)', etc.)

        # List of definitions
        # Each element contains list of tags belonging to that definition
        defn_delimiters = xml_entry.findall('.//m1[b]')
        # Print all delimiters
        # if len(defn_delimiters) > 0: 
        #     print(lemma, *["".join(delim.itertext()) for delim in defn_delimiters])
        for delim in defn_delimiters:
            delim_text = "".join(delim.find("./b").itertext())
            # Remove delimiters that do not define separate definitions
            # (can't use contains() filter in lxml findall() method)
            if not ("I)" in delim_text or "V)" in delim_text): 
                defn_delimiters.remove(delim)
            
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
            # print(lemma, "\n===")
            # print(*["\n".join("".join(elem.itertext()) for elem in defn) for defn in entry_definitions], sep="\n---\n")
            # print()

            # Process each definition separately
            for entry_idx in range(len(entry_definitions)): 
                # Create temporary subentry object to hold elements of a single definition
                defn = etree.Element("subentry")
                defn.extend(entry_definitions[entry_idx])

                defn_num = []
                if len(entry_definitions) > 1: 
                    # Format entry number to match Lewis-Short format
                    # (use brackets for multiple definitions)
                    defn_num.append(f"[{entry_idx}]") 

                new_entry = {
                    "lemma_id": str(lemma_idx),
                    "lemma": lemma,
                    "sense_num": defn_num,
                    "type": "main",  # Main definition
                    "ipa": ipa,
                    "pos": "",
                    "gender": "",
                    "entry": "",
                    "entry_str": "",  # Plaintext of entry (without HTML tags)
                    "gloss": "",
                }

                # Get POS or gender, as applicable
                # Select first <p> tag in entry
                p_tag = defn.find(".//p")
                if p_tag in ["m.", "f.", "n."]: 
                    new_entry["gender"] = p_tag
                    new_entry["pos"] = "n."
                elif p_tag == "a.": 
                    # Normalize 'a.' notation to 'adj.'
                    new_entry["pos"] = "adj."
                else: 
                    # Other tags: adj., adv., pp., prep., interj.
                    new_entry["pos"] = p_tag

                # TODO: get IPA

                # TODO: get entry senses

                # TODO: create XSLT to make HTML-formatted entry

                # TODO: create gloss 
                # (concatenate senses or just use first?)


    except AssertionError as ae: 
        print(f"Assertion failed in entry {lemma}")
    except Exception as e: 
        # lemma = xml_entry.get("entry")
        print(f"Exception in entry {lemma}: {e}")
        raise e