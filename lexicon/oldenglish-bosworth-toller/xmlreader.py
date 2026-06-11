'''
xmlreader.py
XML parser script for the Bosworth and Toller Old English dictionary
'''

import csv, re
from lxml import etree
from time import time
import traceback

import lexdata
from lexdata import ipa_oldenglish
from unescape import unescape

SQL_NULL = "\\N"

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
                if (page_num > 10): 
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
                    prev_entry["entry"] += etree.tostring(line_elem, encoding="Unicode")
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
                while (
                    subtag_idx < len(line_elem) and 
                    line_elem[subtag_idx].tag == "I" and 
                    line_elem[subtag_idx].text in lexdata.ORTH
                ):
                    orthography += line_elem[subtag_idx].text
                    orthography += line_elem[subtag_idx].tail
                    subtag_idx += 1

                # Etymology check 1 - after orthography, before POS
                # If present, will be contained in brackets after orthography or POS
                bracket_idx = orthography.rfind("[")
                remaining = ""
                if bracket_idx != -1: 
                    # Gather etymology data, remove from orth
                    etymology += orthography[bracket_idx:]
                    orthography = orthography[:bracket_idx]
                    bracket_idx = etymology.rfind("]")
                    if bracket_idx == -1:
                        # Collect remaining etymology data
                        while subtag_idx < len(line_elem): 
                            # Check for closing bracket in text node
                            subtag_text = line_elem[subtag_idx].text
                            bracket_idx_text = subtag_text.rfind("]")
                            if bracket_idx_text == -1: 
                                etymology += subtag_text
                            else: 
                                # Etym brackets closed within text node => 
                                # Capture remaining text for gloss/entry
                                etymology += subtag_text[:bracket_idx_text+1]
                                assert gloss == ""
                                gloss = subtag_text[bracket_idx_text+1:]
                                break

                            # Check for closing bracket in tail text
                            subtag_tail = (line_elem[subtag_idx].tail or "")
                            bracket_idx_tail = subtag_tail.rfind("]")
                            if bracket_idx_tail == -1: 
                                etymology += subtag_tail
                            else: 
                                etymology += subtag_tail[:bracket_idx_tail+1]
                                remaining = subtag_tail[bracket_idx_tail+1:].strip()
                                break

                            # Increment idx after checking both text & tail
                            subtag_idx += 1
                            
                        subtag_idx += 1
                    else: 
                        # Closing bracket found in orthography text
                        remaining = etymology[bracket_idx+1:].strip()
                        etymology = etymology[:bracket_idx+1]

                # POS check 1 - after orthography
                if subtag_idx < len(line_elem) and not remaining and line_elem[subtag_idx].tag == "I": 
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
                if subtag_idx < len(line_elem):
                    subtag_text = line_elem[subtag_idx].text or ""
                    subtag_text_words = subtag_text.split()
                    # Find longest matching substring
                    if pos is not None:
                        assert gloss == ""

                        # Check for additional text in POS tag:
                        word_idx = 0
                        while ( " ".join(subtag_text_words[:word_idx+1]) in lexdata.POS_REMOVE and 
                            word_idx <= len(subtag_text_words) ):

                            word_idx += 1
                        gloss_text = " ".join(subtag_text_words[word_idx+1:])
                        if gloss_text.strip() != "":
                            gloss = gloss_text
                            assert entry == ""
                            entry = f"<I>{gloss}</I>"
                            entry += line_elem[subtag_idx].tail or ""
                            entry_str = gloss
                            entry_str += line_elem[subtag_idx].tail or ""
                            subtag_idx += 1
                            # Parse all remaining words into entry field
                            while subtag_idx < len(line_elem): 
                                subtag = line_elem[subtag_idx]
                                entry += etree.tostring(subtag, encoding="Unicode")
                                entry_str += "".join(subtag.itertext()) + (subtag.tail or "")
                                subtag_idx += 1
                            raise EntryCompleted
                            
                # Etymology check 2 - after POS
                if etymology == "" and subtag_idx < len(line_elem): 
                    assert entry == ""
                    assert remaining == ""

                    bracket_idx = line_elem[subtag_idx].tail.rfind("[")
                    if bracket_idx != -1:
                        # Opening bracket found
                        etymology = line_elem[subtag_idx].tail[bracket_idx:]
                        bracket_idx = etymology.rfind("]")
                        if bracket_idx == -1:
                            # Collect remaining etymology data
                            while subtag_idx < len(line_elem): 
                                # Check for closing bracket in text node
                                subtag_text = line_elem[subtag_idx].text
                                bracket_idx_text = subtag_text.rfind("]")
                                if bracket_idx_text == -1: 
                                    etymology += subtag_text
                                else: 
                                    # Etym brackets closed within text node => 
                                    # Capture remaining text for gloss/entry
                                    etymology += subtag_text[:bracket_idx_text+1]
                                    assert gloss == ""
                                    gloss = subtag_text[bracket_idx_text+1:]
                                    break

                                # Check for closing bracket in tail text
                                subtag_tail = (line_elem[subtag_idx].tail or "")
                                bracket_idx_tail = subtag_tail.rfind("]")
                                if bracket_idx_tail == -1: 
                                    etymology += subtag_tail
                                else: 
                                    etymology += subtag_tail[:bracket_idx_tail+1]
                                    remaining = subtag_tail[bracket_idx_tail+1:].strip()
                                    assert remaining == ""
                                    break

                                # Increment idx after checking both text & tail
                                subtag_idx += 1

                            subtag_idx += 1
                        else: 
                            # Closing bracket found in orthography text
                            remaining = etymology[bracket_idx+1:].strip()
                            etymology = etymology[:bracket_idx+1]
                            assert remaining == ""
                
                entry_senses = []
                if subtag_idx < len(line_elem):
                    # Check for multiple senses
                    if ( line_elem[subtag_idx].tag == "B" and 
                        re.match(r'^[IVX][IVX]?I?I?\.', line_elem[subtag_idx].text) ):
                        entry_senses = parse_senses(line_elem, subtag_idx, {"lemma_idx": lemma_idx, "lemma": lemma, "page_num": page_num})
                        raise EntryCompleted

                    else: 
                        # Parse (single) entry & gloss
                        if entry == "":
                            if remaining:
                                entry += remaining
                                print(f"LEMMA {lemma} + REMAINING {remaining}")
                            
                            if subtag_idx < len(line_elem):
                                subtag_text = line_elem[subtag_idx].text or ""
                                subtag_text_words = subtag_text.split()
                                # Entry case 1: gloss included in <I> with POS
                                # Find longest matching substring
                                if subtag_text_words[0] in lexdata.POS_REMOVE:
                                    assert gloss == ""
                                    
                                    word_idx = 0
                                    while ( " ".join(subtag_text_words[:word_idx+1]) in lexdata.POS_REMOVE and 
                                        word_idx <= len(subtag_text_words) ):

                                        word_idx += 1
                                    gloss_text = " ".join(subtag_text_words[word_idx+1:])
                                    if gloss_text.strip() != "":
                                        gloss = gloss_text
                                        assert entry == ""
                                        entry = f"<I>{gloss}</I>"
                                        entry += line_elem[subtag_idx].tail or ""
                                        entry_str = gloss
                                        entry_str += line_elem[subtag_idx].tail or ""
                                        subtag_idx += 1

                            # Parse remaining data
                            # Case 3: no remaining child tags; entry is remaining tail text
                            if subtag_idx >= len(line_elem) and entry == "": 
                                print("PARSE REMAINING")
                                entry = line_elem[-1].tail
                                entry_str = line_elem[-1].tail
                                raise EntryCompleted
                            
                            # Case 2: gloss in isolated tag (and not yet parsed)
                            if gloss == "" and line_elem[subtag_idx].tag == "I":
                                gloss = line_elem[subtag_idx].text
                            while subtag_idx < len(line_elem): 
                                subtag = line_elem[subtag_idx]
                                entry += etree.tostring(subtag, encoding="Unicode")
                                entry_str += "".join(subtag.itertext()) + (subtag.tail or "")
                                subtag_idx += 1
                            raise EntryCompleted

            except IndexError as ie: 
                print(f"IndexError in lemma {lemma}: {ie}")
                print(lemma, gloss, orthography, etymology, pos, entry, sep="\n")
                save_csv(dict_entries, "bosworth-toller-error.csv")
                raise ie  # Fail loudly
                # Fail quietly; process other entries
                print(f"IndexError in lemma {lemma}: {ie}")  
                continue  # Don't append entry to output list
            except AssertionError as ae: 
                # Pass assertion errors -- TO REMEDIATE MANUALLY
                print("ASSERTION ERROR: lemma", lemma)
                print(traceback.format_exc())
            except EntryCompleted:
                # All XML elements parsed; jump to entry creation
                # print("Entry completed:", lemma)
                pass

            # Debug exception handler:
            # Prints values for current lemma & outputs
            # partial dict to 'bosworth-toller-error.csv'
            except Exception as e:
                print(f"Exception in lemma {lemma}: {e}")
                print(lemma, gloss, orthography, etymology, pos, entry, sep="\n")
                save_csv(dict_entries, "bosworth-toller-error.csv")
                raise e  # Fail loudly

            # TODO: Try to impute POS if missing
            # Check gloss (e.g. begins with "To _" or "A/an _")
            # or orthography (pp. --> verb, dat. --> noun)

            # Final cleanup
            etymology = etymology.strip()
            orthography = orthography.strip(" ,;")
            gloss = gloss.strip(" ,;")
            gender = gender.replace(",", ".")
            entry = f'<div class="oldenglish bodytext">{entry.strip()}</div>'
            entry_str = entry_str.strip()

            if not entry_senses:
                # Single entry sense
                new_entry = {
                    "lemma_id": str(lemma_idx),
                    "lemma": lemma,
                    "sense_num": "",
                    "page_num": str(page_num),
                    "type": "main",
                    "ipa": ipa,
                    "orth": orthography,
                    "pos": pos,
                    "gender": gender,
                    "etym": etymology,
                    "entry": entry,
                    "entry_str": entry_str,  # Plaintext of entry (without XML tags)
                    "gloss": gloss,
                }
            else: 
                # Multiple entry senses
                # Take main entry from first sense
                first_sense = entry_senses.pop(0)
                new_entry = {
                    "lemma_id": str(lemma_idx),
                    "lemma": lemma,
                    "sense_num": first_sense["sense_num"],
                    "page_num": str(page_num),
                    "type": "main",
                    "ipa": ipa,
                    "orth": orthography,
                    "pos": pos,
                    "gender": gender,
                    "etym": etymology,
                    "entry": first_sense["entry"],
                    "entry_str": first_sense["entry_str"],  # Plaintext of entry (without XML tags)
                    "gloss": first_sense["gloss"],
                }

            new_entries = [ new_entry ] + entry_senses

            # Set prev_entry
            if dict_entries: 
                prev_entry = new_entry

            # Handle empty fields, append to dict
            for entry in new_entries:
                for k,v in entry.items():
                    if v == "":
                        entry[k] = SQL_NULL
                dict_entries.append(entry)
                
    return dict_entries

def parse_senses(line_elem, subtag_idx, lemma_info):
    '''
    Parse and return a list of senses in the provided xml_line element
    Assumes subtag_idx points to a <B> tag in line_elem that begins
    the first dictionary sense.
    Lemma_info is a dict containing lemma_idx, lemma, and page_num 
    from main entry

    Returns a list of sense objects, matching the schema for other 
    dictionary entries above. 
    '''
    entry_senses = []
    if line_elem[subtag_idx].tag != "B": 
        raise ValueError("Init. subtag_idx does not point to <B> tag! (in parse_senses)")
    if not re.match(r'^[IVX][IVX]?I?I?\.', line_elem[subtag_idx].text):
        raise ValueError("Init. <B> tag does not contain sense_num")

    while subtag_idx < len(line_elem):
        # Parse out the rest of the line
        new_sense = {
            "lemma_id": str(lemma_info["lemma_idx"]),
            "lemma": lemma_info["lemma"],
            "sense_num": "",  # Filled in below
            "page_num": str(lemma_info["page_num"]),
            "type": "sense",
            # Unique fields
            "entry": "",
            "entry_str": "",
            "gloss": "",
            # Intentionally left blank
            "ipa": "",
            "orth": "",
            "pos": "",
            "gender": "",
            "etym": "",
        }
        if not re.match(r'^[IVX][IVX]?I?I?\.', line_elem[subtag_idx].text):
            raise ValueError(f"<B> tag does not contain sense_num. Text contents: {line_elem[subtag_idx].text}")
        new_sense["sense_num"] = line_elem[subtag_idx].text.strip(".")

        if line_elem[subtag_idx].tail is not None and line_elem[subtag_idx].tail.strip() != "": 
            print(new_sense["lemma"], new_sense["sense_num"])
            raise ValueError(f"Sense_num tag tail is nonnull. Contents: {line_elem[subtag_idx].tail}")

        subtag_idx += 1
        if line_elem[subtag_idx].tag != "I":
            print(new_sense["lemma"], new_sense["sense_num"])
            raise ValueError(f"Gloss not found for sense; first tag was not <I>. Tag: {"".join(line_elem[subtag_idx].itertext())}")

        # Parse gloss, entry
        new_sense["gloss"] = line_elem[subtag_idx].text
        new_sense["entry"] += "".join(line_elem[subtag_idx].itertext()) + (line_elem[subtag_idx].tail or "")
        new_sense["entry_str"] += line_elem[subtag_idx].text + (line_elem[subtag_idx].tail or "")
        subtag_idx += 1

        while subtag_idx < len(line_elem) and line_elem[subtag_idx].tag != "B":
            # Parse rest of sense
            new_sense["entry"] += "".join(line_elem[subtag_idx].itertext()) + (line_elem[subtag_idx].tail or "")
            new_sense["entry_str"] += line_elem[subtag_idx].text + (line_elem[subtag_idx].tail or "")
            subtag_idx += 1

        entry_senses.append(new_sense)

    return entry_senses

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
