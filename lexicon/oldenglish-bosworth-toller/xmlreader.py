'''
xmlreader.py
XML parser script for the Bosworth and Toller Old English dictionary
'''

import csv, html
from lxml import etree
from time import time

def line_xml(raw_line, wrapper_tag = "xml_line"):
    '''
    Generates an lxml.etree.Element instance
    from a line of text which has XML syntax
    but is not wrapped in an XML tag.

    Optional argument wrapper_tag can be used
    to set the name of the wrapper element.

    Intended to help parse Bosworth-Toller line-by-line.
    '''
    xml_str = f"<{wrapper_tag}>{raw_line}</{wrapper_tag}>"
    elem = etree.XML(xml_str)
    return elem

def get_entries(filename):
    '''
    Return a dict of entries from the provided
    XML file
    '''
    page_num = None  # Page number counter

    with open(filename, 'r') as f: 
        for line in f: 
            # Strip trailing newline from line
            line = line.strip()
            
            if line == "": 
                # Ignore empty lines
                continue
            elif line.startswith("<PAGE NUM="):
                # Check for page tag (invalid XML)
                page_num = int(line[12:16])
                print("Page", page_num)
                if (page_num > 1): 
                    break
                continue

            # Escape HTML characters
            line_unicode = html.unescape(line)
            line_elem = line_xml(line_unicode)


            
    return None

def save_csv(data, filename):
    fieldnames = ["lemma_id", "lemma", "sense_num", "type", "ipa", "pos", "gender", "entry", "entry_str", "gloss"]
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
        "gloss": ent["gloss"]
        } for ent in data]
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(rows)  # Write data rows

if __name__ == "__main__":
    startTime = time()
    entries = get_entries("bosworth-toller-1989.xml")
    save_csv(entries, "bosworth-toller.csv")
    print("Parsing completed.")
    print("Runtime:", time() - startTime, "s")
