'''
xmlreader.py
XML parser script for the Bosworth and Toller Old English dictionary
'''

import sys

import csv
from lxml import etree
from time import time

import lexdata
from lexdata import ipa_oldenglish
from unescape import unescape

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
    dict_entries = []
    page_num = None  # Page number counter
    lemma_idx = 1 # Start indexing at 1 to match SQL convention

    with open(filename, 'r') as f: 
        for line in f: 
            # Strip trailing newline from line
            line = line.strip()
            
            if line == "": 
                # Ignore empty lines
                continue
            elif (
                line.startswith("<letterheader>") or 
                line.startswith("<HEADER>")
            ): 
                # Ignore header tags
                prev_entry = None
                continue
            elif line.startswith("<PAGE NUM="):
                # Check for page tag (invalid XML - won't parse)
                # Extract page number for entries
                page_num = int(line[12:16])
                print("Page", page_num)
                if (page_num > 1): 
                    break
                prev_entry = None
                continue

            # Escape HTML characters
            line_unicode = unescape(line)
            line_elem = line_xml(line_unicode)

            # Check for initial text node or
            # initial <I> tag => entry overflow
            # from previous line/page
            # (append text to previous entry)
            if (
                line_elem.text is not None or 
                line_elem[0].tag != "B"
            ):
                if prev_entry is None: 
                    # If no preceding data or preceding header
                    continue
                else: 
                    print("".join(line_elem.itertext()))
                    continue

            # Ordinary entry line
            if line_elem[0].tag != "B": 
                raise ValueError(f"Line does not start with <B> tag: {line_unicode}")
            else: 
                lemma = line_elem[0].text.strip(" \n,;")
                ipa = ipa_oldenglish(lemma)

            # Scan though entry to extract data
            subtag_idx = 1

            try: 
                orthography = lemma
                etymology = ""
                # Check for additional orthographical information
                if line_elem[0].tail and len(line_elem) > 1: 
                    orthography += line_elem[0].tail
                while (
                    line_elem[subtag_idx].tag == "I" and 
                    line_elem[subtag_idx].text in lexdata.ORTH
                ):
                    orthography += line_elem[subtag_idx].text
                    orthography += line_elem[subtag_idx].tail
                    subtag_idx += 1

                # Etymology check 1 - after orthography
                # If present, will be contained in brackets after orthography or POS
                bracket_idx = orthography.rfind("[")
                if bracket_idx != -1: 
                    # Gather etymology data, remove from orth
                    etymology += orthography[bracket_idx:]
                    orthography = orthography[:bracket_idx]
                    # Collect remaining etymology data
                    while True: 
                        if line_elem[subtag_idx].text is not None: 
                                bracket_idx_text = line_elem[subtag_idx].text.rfind("]")
                                if bracket_idx_text == -1: 
                                    etymology += line_elem[subtag_idx].text
                                else: 
                                    etymology += line_elem[subtag_idx].text[:bracket_idx_text+1]
                                    break
                        if line_elem[subtag_idx].tail is not None: 
                            bracket_idx_tail = line_elem[subtag_idx].tail.rfind("]")
                            if bracket_idx_text == -1: 
                                etymology += line_elem[subtag_idx].tail
                            else: 
                                etymology += line_elem[subtag_idx].tail[:bracket_idx_text+1]
                                break
                            subtag_idx += 1
                        subtag_idx += 1

                # POS check 1 - after orthography
                pos = None
                if line_elem[subtag_idx].tag == "I": 
                    subtag_text = line_elem[subtag_idx].text
                    word_0 = subtag_text.split()[0]
                    if word_0 in lexdata.POS: 
                        pos = word_0
                    elif word_0 in lexdata.POS_IMPLIES_V: 
                        pos = "v. " + word_0
                    elif word_0 in lexdata.POS_IMPLIES_N: 
                        pos = "n. " + word_0
                    elif ( len(subtag_text.split()) > 1 and 
                        word_0 in lexdata.POS_W_GLOSS):
                        pos = "n. " + word_0
                
                # Etymology check 2 - after POS
                if etymology == "": 
                    bracket_idx = line_elem[subtag_idx].tail.rfind("[")
                    if bracket_idx != -1: 
                        # Gather etymology data
                        etymology += line_elem[subtag_idx].tail[bracket_idx:]
                        orthography = line_elem[subtag_idx].tail[:bracket_idx]
                        subtag_idx += 1
                        # Collect remaining etymology data (scan until closing bracket found)
                        while True: 
                            if line_elem[subtag_idx].text is not None: 
                                bracket_idx_text = line_elem[subtag_idx].text.rfind("]")
                                if bracket_idx_text == -1: 
                                    etymology += line_elem[subtag_idx].text
                                else: 
                                    etymology += line_elem[subtag_idx].text[:bracket_idx_text+1]
                                    break
                            if line_elem[subtag_idx].tail is not None: 
                                bracket_idx_tail = line_elem[subtag_idx].tail.rfind("]")
                                if bracket_idx_text == -1: 
                                    etymology += line_elem[subtag_idx].tail
                                else: 
                                    etymology += line_elem[subtag_idx].tail[:bracket_idx_text+1]
                                    break
                            subtag_idx += 1
                
                # Etym & orth final cleanup
                etymology = etymology.strip()
                orthography = orthography.strip(" ,;")
                
            except IndexError as ie: 
                raise ie  # Fail loudly
                print(f"IndexError in lemma {lemma}: {ie}")  # Fail quietly; process other entries
                continue  # Don't append entry to output list

            new_entry = {
                "lemma_id": str(lemma_idx),
                "lemma": lemma,
                "sense_num": [],
                "page_num": str(page_num),
                "type": "main",
                "ipa": ipa,
                "orth": "",
                "pos": "",
                "gender": "",
                "etym": "",
                "entry": "",
                "entry_str": "",  # Plaintext of entry (without XML tags)
                "gloss": "",
            }
            
            # Set prev_entry
            # Append new entry to dict_entries
            
            # DEV: Abort execution 
            sys.exit()
            
    return dict_entries

def save_csv(data, filename):
    fieldnames = ["lemma_id", "lemma", "sense_num", "page_num", "type", "ipa", "orthography", "pos", "gender", "etymology", "entry", "entry_str", "gloss"]
    rows = [{
        "lemma_id": ent["lemma_id"],
        "lemma": ent["lemma"], 
        "sense_num": ent["sense_num"],
        "page_num": ent["page_num"],
        "type": ent["type"],
        "ipa": ent["ipa"], 
        "orthography": ent["orth"], 
        "pos": ent["pos"],
        "gender": ent["gender"],
        "etymology": ent["etym"],
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
