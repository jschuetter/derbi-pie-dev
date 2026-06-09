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

class EntryCompleted(Exception):
    '''Custom Exception to denote all XML in line has been parsed'''
    pass

def get_entries(filename):
    '''
    Return a dict of entries from the provided
    XML file
    '''
    dict_entries = []
    page_num = None  # Page number counter
    prev_entry = None
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
                continue
            elif line.startswith("<PAGE NUM="):
                # Check for page tag (invalid XML - won't parse)
                # Extract page number for entries
                page_num = int(line[12:16])
                # DEV: stop after page 5
                if (page_num > 5): 
                    break
                print("Page", page_num)
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
                    # Append data to previous entry
                    prev_entry["entry_str"] += "".join(line_elem.itertext()) + (line_elem.tail or "")
                    prev_entry["entry"] += etree.tostring(line_elem).decode("utf-8")
                    continue

            # Ordinary entry line
            if line_elem[0].tag != "B": 
                raise ValueError(f"Line does not start with <B> tag: {line_unicode}")
            else: 
                lemma = line_elem[0].text.strip(" \n,;")
                ipa = ipa_oldenglish(lemma)
                orthography = line_elem[0].text  # Add lemma with punctuation to orthography var

            # Scan though entry to extract data
            subtag_idx = 1

            try: 
                # Declare variables for entry fields
                etymology = ""
                pos = None
                gender = ""
                entry = ""
                entry_str = ""
                gloss = ""

                # Handle single-tag lines
                if len(line_elem) == 1:
                    if line_elem[0].tail:
                        gloss = entry_str = entry = line_elem[0].tail
                        raise EntryCompleted
                    
                # Check for additional orthographical information
                if line_elem[0].tail: 
                    orthography += line_elem[0].tail
                print(len(line_elem))
                while (
                    subtag_idx < len(line_elem) and 
                    line_elem[subtag_idx].tag == "I" and 
                    line_elem[subtag_idx].text in lexdata.ORTH
                ):
                    orthography += line_elem[subtag_idx].text
                    orthography += line_elem[subtag_idx].tail
                    subtag_idx += 1

                # Etymology check 1 - after orthography
                # If present, will be contained in brackets after orthography or POS
                bracket_idx = orthography.rfind("[")
                remaining = ""
                if bracket_idx != -1: 
                    # Gather etymology data, remove from orth
                    etymology += orthography[bracket_idx:]
                    orthography = orthography[:bracket_idx]
                    print("Orthography clipped to", bracket_idx)
                    bracket_idx = etymology.rfind("]")
                    if bracket_idx == -1:
                        # Collect remaining etymology data
                        while subtag_idx < len(line_elem): 
                            subtag_str = "".join(line_elem[subtag_idx].itertext()) + (line_elem[subtag_idx].tail or "")
                            bracket_idx = subtag_str.rfind("]")
                            print(bracket_idx, subtag_str)
                            if bracket_idx == -1: 
                                etymology += subtag_str
                                subtag_idx += 1
                            else: 
                                etymology += subtag_str[:bracket_idx+1]
                                remaining = subtag_str[bracket_idx+1:].strip()
                                break
                    else: 
                        etymology = etymology[:bracket_idx+1]
                        remaining = etymology[bracket_idx+1:].strip()

                # POS check 1 - after orthography
                if not remaining and line_elem[subtag_idx].tag == "I": 
                    subtag_text = line_elem[subtag_idx].text
                    subtag_words = subtag_text.split()
                    if subtag_words[0] in lexdata.POS: 
                        word_idx = 1
                        while ( 
                            " ".join(subtag_words[:word_idx+1]) in lexdata.POS and 
                            word_idx < len(subtag_words)
                            ):
                            word_idx += 1
                        pos = " ".join(subtag_words[:word_idx])
                    elif subtag_words[0] in lexdata.POS_IMPLIES_V: 
                        pos = "v. " + subtag_words[0]
                    elif subtag_words[0] in lexdata.POS_IMPLIES_N: 
                        pos = "n."
                        gender = subtag_words[0]
                    elif ( len(subtag_words) > 1 and 
                        subtag_words[0] in lexdata.POS_W_GLOSS ):
                        if " ".join(subtag_words[:2]) in lexdata.POS_W_GLOSS:
                            pos = "n. " + subtag_words[0]
                            gender = subtag_words[1]
                        else: 
                            pos = "n. " + subtag_words[0]
                            
                # Parse entry & gloss case 1: gloss included in <I> with POS
                subtag_text = line_elem[subtag_idx].text or ""
                subtag_text_words = subtag_text.split()
                # Find longest matching substring
                if pos is not None:
                    word_idx = 0
                    while subtag_text_words[:word_idx+1] in lexdata.POS_REMOVE:
                        word_idx += 1
                    gloss = " ".join(subtag_text_words[word_idx+1:])
                    assert entry == ""
                    entry = f"<I>{gloss}</I>"
                    entry += line_elem[subtag_idx].tail or ""
                    entry_str = gloss
                    entry_str += line_elem[subtag_idx].tail or ""
                    subtag_idx += 1
                    # Parse all remaining words into entry field
                    while subtag_idx < len(line_elem): 
                        subtag = line_elem[subtag_idx]
                        entry += etree.tostring(subtag).decode("utf-8")
                        entry_str += "".join(subtag.itertext()) + (subtag.tail or "")
                        subtag_idx += 1
                    raise EntryCompleted
                            
                # Etymology check 2 - after POS
                if etymology == "" and subtag_idx < len(line_elem): 
                    assert entry == ""
                    assert remaining == ""

                    bracket_idx = line_elem[subtag_idx].tail.rfind("[")
                    if bracket_idx != -1: 
                        # Gather etymology data, remove from orth
                        etymology += line_elem[subtag_idx].tail[bracket_idx:]
                        bracket_idx = etymology.rfind("]")
                        if bracket_idx == -1:
                            # Collect remaining etymology data
                            while subtag_idx < len(line_elem): 
                                subtag_str = "".join(line_elem[subtag_idx].itertext()) + (line_elem[subtag_idx].tail or "")
                                bracket_idx = subtag_str.rfind("]")
                                if bracket_idx == -1: 
                                    etymology += subtag_str
                                    subtag_idx += 1
                                else: 
                                    etymology += subtag_str[:bracket_idx+1]
                                    remaining = subtag_str[bracket_idx+1:].strip()
                                    if remaining != "":
                                        raise ValueError(f"Etym remaining non-empty! Lemma: {lemma}\nRemaining text: {remaining}")
                                    break
                        else: 
                            etymology = etymology[:bracket_idx+1]
                            remaining = etymology[bracket_idx+1:].strip()
                            if remaining != "":
                                raise ValueError(f"Etym remaining non-empty! Lemma: {lemma}\nRemaining text: {remaining}")
                
                # TODO: add check for multiple senses
                # TODO: check for add'l POS in sense?  => multiple entries, instead of multiple senses?

                # Parse entry & gloss
                if entry == "":
                    if remaining:
                        entry += remaining
                    
                    subtag_text = line_elem[subtag_idx].text or ""
                    subtag_text_words = subtag_text.split()
                    # Entry case 1: gloss included in <I> with POS
                    # Find longest matching substring
                    if subtag_text_words[0] in lexdata.POS_REMOVE:
                        word_idx = 0
                        while subtag_text_words[:word_idx+1] in lexdata.POS_REMOVE:
                            word_idx += 1
                        gloss = " ".join(subtag_text_words[word_idx+1:])
                        assert entry == ""
                        entry = f"<I>{gloss}</I>"
                        entry += line_elem[subtag_idx].tail or ""
                        entry_str = gloss
                        entry_str += line_elem[subtag_idx].tail or ""
                        subtag_idx += 1

                    # Parse remaining data
                    # Case 3: no remaining child tags; entry is remaining tail text
                    if subtag_idx == len(line_elem) + 1 and entry == "": 
                        entry = line_elem[subtag_idx].tail
                        entry_str = line_elem[subtag_idx].tail
                    # (Also case 2: gloss in isolated tag)
                    if gloss == "" and line_elem[subtag_idx].tag == "I":
                        gloss = line_elem[subtag_idx].text
                    while subtag_idx < len(line_elem): 
                        subtag = line_elem[subtag_idx]
                        entry += etree.tostring(subtag).decode("utf-8")
                        entry_str += "".join(subtag.itertext()) + (subtag.tail or "")
                        subtag_idx += 1

                # Try to impute POS if missing
                # Check gloss (e.g. begins with "To _" or "A/an _")
                # or orthography (pp. --> verb, dat. --> noun)

                # Final cleanup
                etymology = etymology.strip()
                orthography = orthography.strip(" ,;")
                gloss = gloss.strip(" ,;")
                gender = gender.replace(",", ".")
                
            except IndexError as ie: 
                print(f"IndexError in lemma {lemma}: {ie}")  # Fail quietly; process other entries
                raise ie  # Fail loudly
                print(f"IndexError in lemma {lemma}: {ie}")  # Fail quietly; process other entries
                continue  # Don't append entry to output list
            except EntryCompleted:
                # All XML elements parsed; jump to entry creation
                pass

            new_entry = {
                "lemma_id": str(lemma_idx),
                "lemma": lemma,
                "sense_num": [],
                "page_num": str(page_num),
                "type": "main",
                "ipa": ipa,
                "orth": orthography,
                "pos": pos or "NONE",
                "gender": gender,
                "etym": etymology,
                "entry": entry,
                "entry_str": entry_str,  # Plaintext of entry (without XML tags)
                "gloss": gloss,
            }
            
            # Set prev_entry
            # Append new entry to dict_entries
            if dict_entries: 
                prev_entry = dict_entries[-1]
            dict_entries.append(new_entry)
            
            # DEV: Abort execution 
            # sys.exit()
            
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
    save_csv(entries, "bosworth-toller-test.csv")
    print("Parsing completed.")
    print("Runtime:", time() - startTime, "s")
