'''
xmlreader.py

Python script to read dictionary XML file for 
Monier-Williams Sanskrit-English dictionary
'''

import csv, re
from lxml import etree
from time import time

# XSLT_DOC = "./monier-williams-template.xslt"
SQL_NULL = "\\N"

def get_entries(filename): 
    '''
    Return a dict of entries from the provided
    XML file
    '''
    parser = etree.XMLParser(load_dtd=True, no_network=False)
    tree = etree.parse(filename, parser=parser)
    root = tree.getroot()  # <mw> entry
    
    # Zoega dictionary XML does not include the following fields: 
    # page_num, orthography, components, stem, etymology

    # Lang code, editor, updated date fields will be filled in when
    # importing to MySQL

    dict_entries = []
    # xslt_tree = etree.parse(XSLT_DOC)
    # xslt = etree.XSLT(xslt_tree)
    
    # HANDLE INDEXING CASE-BY-CASE -- PRESERVE EXISTING INDEXES
    # Query next available lemma indexes from MySQL
    next_lemma_idx = None
    next_sense_idx = None

    prev_entry = None
    prev_main_entry = None
    
    # Parse XML line-by-line
    # Cases: 
    #   1. Create new headword entry
    #       - If subordinate: link to headword entry
    #   2. Create new sense entry
    #   3. Append to previous entry

    for entry in root: 
        # Entry has 1 of 13 root tags; will determine course of action
        # Case 1: new headword (<H1>)
        # Create new headword
        if entry.tag == "H1":
            pass
        # Case 2: subordinate headword (<H2>, <H3>, <H4>)
        # Create new headword, link to primary entry
        elif re.match(r'H[2-4]', entry.tag):
            pass
        # Case 3: sub-sense of previous entry (<H1A>, <H2A>, <H2B>, etc.)
        # Append text to previous entry
        elif re.match(r'H[1-4][A-B]', entry.tag):
            pass
        else: 
            raise ValueError(f"Unexpected entry root tag: {entry.tag}")


    # N.B. QUERY EXISTING IDs FROM MySQL
        
    return dict_entries

def save_csv(data, filename):
    fieldnames = ["lemma_id", "lemma", "sense_num", "type", "ipa", "pos", "gender", "entry", "entry_str", "gloss", "sense_id", "h_num", "parent_h_num"]
    rows = [{
        "lemma_id": ent["lemma_id"],
        "lemma": ent["lemma"], 
        "sense_num": ent["sense_num"],
        "type": ent["type"],
        "ipa": ent["ipa"], 
        "pos": ent["pos"],
        "gender": ent["gender"],
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
    startTime = time()
    entries = get_entries("monier-williams.xml")
    save_csv(entries, "monier-williams.csv")
    print("Parsing completed.")
    print("Runtime:", time() - startTime, "s")
