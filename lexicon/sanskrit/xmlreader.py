'''
xmlreader.py

Python script to read dictionary XML file for 
Monier-Williams Sanskrit-English dictionary
'''

import csv
from lxml import etree
from time import time

# XSLT_DOC = "./zoega-template.xslt"
SQL_NULL = "\\N"

def get_entries(filename): 
    '''
    Return a dict of entries from the provided
    XML file
    '''
    parser = etree.XMLParser(load_dtd=True, no_network=False)
    tree = etree.parse(filename, parser=parser)
    root = tree.getroot()
    
    # Zoega dictionary XML does not include the following fields: 
    # page_num, orthography, components, stem, etymology

    # Lang code, editor, updated date fields will be filled in when
    # importing to MySQL

    dict_entries = []
    xslt_tree = etree.parse(XSLT_DOC)
    xslt = etree.XSLT(xslt_tree)
    lemma_idx = 1 # Start indexing at 1 to match SQL convention
    sense_idx = 1
    
    # Parse XML line-by-line
    # Cases: 
    #   1. Create new headword entry
    #       - If subordinate: link to headword entry
    #   2. Create new sense entry
    #   3. Append to previous entry


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
