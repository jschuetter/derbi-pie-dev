"""
iterReader.py
Modified version of CLTK Lewis Latin lexicon XML reader to convert to CSV
Original source: https://github.com/cltk/cltk_lat_lewis_elementary_lexicon/
"""
# import codecs

from lxml import etree
import csv
from time import time
from lexdata import *

def get_root(filename):
    parser = etree.XMLParser(load_dtd=True, no_network=False)
    tree = etree.parse(filename, parser=parser)
    return tree.getroot()

def get_entries(filename):
    root = get_root(filename)
    lemmata = set()
    d = []
    sqlNull = "\\N"
    # Start indexes at 1 to match SQL convention
    lemma_idx = 1
    cur_page = 1  # Current page number
    for xml_entry in root.findall(".//entryFree"):
        try:
            # print("Entry:", entry)
            lemma = xml_entry.get("key", "")
            new_entry = {
                "lemma_id": str(lemma_idx),
                "lemma": lemma,
                "sense_num": "",  # Default to primary sense
                "page_num": str(cur_page),
                "type": "",
                "orth": "",
                "pos": "",
                "etym": "",
                "entry": "",
                "entry_plain": ""  # Plaintext of entry (without XML tags)
            }
            new_subentries = []    # Initialize this here to avoid double-adding subentries if exception triggered

            # Use XPath to parse entry type
            new_entry["type"] = xml_entry.get("type", "")

            # Iterate through all tags in entry, parse appropriate data
            idx = 0
            child = xml_entry[idx]
            # Orthography + principal parts
            if child.tag == "orth":
                new_entry["orth"] += (child.text if child.text else "")
                idx += 1
                while idx < len(xml_entry):
                    child = xml_entry[idx]
                    # Child is in accepted tags, append text & preceding tail, continue loop
                    if child.tag in ["orth", "itype", "bibl"]:  # Add <bibl> tag to accepted list, see 'Aaron' - 22 Sep 2025
                        new_entry["orth"] += xml_entry[idx-1].tail if xml_entry[idx-1].tail else ""
                    else:
                        break
                    
                    new_entry["orth"] += "".join(child.itertext())
                    idx += 1
                
                # Handle case where no other tags follow orth
                if idx >= len(xml_entry):
                    if child.tail:
                        new_entry["entry"] += child.tail.lstrip("., ").rstrip()
                        new_entry["entry_plain"] += child.tail.lstrip("., ").rstrip()
                    continue  # Move to next entry
                    
            else: 
                new_entry["orth"] = sqlNull

            # Gender OR pos -- should only be 1?
            # Parse from tag contents only
            genTag = xml_entry.find("gen")
            posTag = xml_entry.find("pos")
            if genTag is not None and posTag is not None: 
                # raise ValueError(f"Entry {lemma} has both <gen> and <pos> tags")
                # Take first chronologically
                if xml_entry.index(genTag) < xml_entry.index(posTag):   
                    new_entry["pos"] = "n. " + (genTag.text if genTag.text else "")
                else: 
                    new_entry["pos"] = (posTag.text if posTag.text else "")
            else: 
                if genTag is None and posTag is None: 
                    # If not found, search descendants
                    genTag = xml_entry.find(".//gen")
                    posTag = xml_entry.find(".//pos")

                if genTag is not None: 
                    new_entry["pos"] = "n. " + (genTag.text if genTag.text else "")
                elif posTag is not None: 
                    new_entry["pos"] = (posTag.text if posTag.text else "")
                else: 
                    # If still not found, set to Null
                    new_entry["pos"] = sqlNull

            # Parse etym tag -- should only be 1
            etymTags = xml_entry.findall("etym")
            if etymTags is None or len(etymTags) <= 0: 
                # If not found, check descendants
                etymTags = xml_entry.findall(".//etym")
                if etymTags is not None and len(etymTags) >= 1: 
                    new_entry["etym"] = "".join(etymTags[0].itertext())
                else: 
                    new_entry["etym"] = sqlNull
            else: 
                # Take first tag only
                # Parse entire contents of <etym> tag, including any <foreign> tags
                new_entry["etym"] = "".join(etymTags[0].itertext())


            while idx < len(xml_entry):
                child = xml_entry[idx]
                if child.tag in ["gen", "pos", "etym"]:
                    # Ignore contents
                    idx += 1
                    continue
                else: 
                    break

            # Append tail to entry definition
            child = xml_entry[idx-1]
            new_entry["entry"] += (child.tail if child.tail else "").lstrip("., ").rstrip()
            new_entry["entry_plain"] += (child.tail if child.tail else "").lstrip("., ").rstrip()

            # Parse remaining text in XML format as definition
            # N.B. quotes will be encoded in CSV doubled ( " --> "" )
            while idx < len(xml_entry):
                child = xml_entry[idx]
                # Remove <foreign> tags - ??
                # if child.tag == "foreign":
                #     new_entry["entry"] += "".join(child.itertext())
                #     if child.tail: 
                #         new_entry["entry"] += child.tail
                # else: 
                #     new_entry["entry"] += etree.tostring(child, encoding="unicode", with_tail=True) #, pretty_print=True) <-- messes up CSV formatting?
                new_entry["entry_plain"] += "".join(child.itertext())
                if child.tail: 
                    new_entry["entry_plain"] += child.tail
                idx += 1

            # Get all sense tags as sub-entries
            # All common fields are Null
            cur_sense_num = ["I"]
            for sense_tag in xml_entry.findall(".//sense"):
                new_subentry = {
                    "lemma_id": str(lemma_idx),
                    "lemma": lemma,
                    "sense_num": "",
                    "page_num": str(cur_page),
                    "type": "sense",
                    "orth": sqlNull,
                    "pos": sqlNull,
                    "etym": sqlNull,
                    "entry": etree.tostring(sense_tag, encoding="unicode", with_tail=True),
                    "entry_plain": "".join(sense_tag.itertext())  # Plaintext of entry (without XML tags)
                }
                if sense_tag.tail:
                    new_subentry["entry_plain"] += sense_tag.tail
                # Parse sense level & number data
                sense_lvl = int(sense_tag.get("level"))
                sense_num = sense_tag.get("n")
                # Pad or truncate cur_sense_num to match subentry level
                if len(cur_sense_num) < sense_lvl: 
                    while len(cur_sense_num) < sense_lvl: 
                        cur_sense_num.append("X")
                    cur_sense_num[sense_lvl-1] = sense_num
                else: 
                    while len(cur_sense_num) > sense_lvl:
                        cur_sense_num.pop()
                    cur_sense_num[sense_lvl-1] = sense_num
                new_subentry["sense_num"] = '.'.join(cur_sense_num)

                # Add entry as child of parent
                new_subentries.append(new_subentry)

                # Check for page break in entry
                page_break_tag = sense_tag.findall(".//pb")
                if page_break_tag: 
                    # If found, update to highest page number seen
                    cur_page = page_break_tag[-1].get("n")
                
            # Assign Entry fields of first subentry to main entry and remove
            if new_subentries: 
                new_entry["entry"] = new_subentries[0]["entry"]
                new_entry["entry_plain"] = new_subentries[0]["entry_plain"]
                # Handle case without duplicate "I" sense_num
                new_subentries.pop(0)
                if new_subentries and new_subentries[0]["sense_num"] != "I":
                    new_entry["sense_num"] = "I"

                
        except IndexError as ie:
            print(f"IndexError in entry {lemma}: {ie}")
        except Exception as e: 
            print(f"Exception in entry {lemma}\n{e}")
        finally:
            # Continue to next entry if end of entry is reached
            new_entries = [new_entry] + new_subentries
            for ne in new_entries: 
                for k,v in ne.items():
                    if isinstance(v, list):     # Convert chlid_ids to str 
                        v = ",".join(v)
                    if v == "": 
                        ne[k] = sqlNull
                    else: 
                        ne[k] = v.strip(" ,").lstrip(".") # Clean up leading/trailing punctuation
                        # Close unclosed parentheses
                        openParens = ne[k].count("(")
                        closeParens = ne[k].count(")")
                        if openParens > closeParens:
                            ne[k] += ")" * (openParens - closeParens)
                        elif closeParens > openParens:
                            ne[k] = "(" * (closeParens - openParens) + ne[k]
                d.append(ne)

            # Check for page break in entry
            # N.B. first updated when searching subentries - this may not do anything
            page_break_tag = xml_entry.findall(".//pb")
            if page_break_tag: 
                # If found, update to highest page number seen
                cur_page = page_break_tag[-1].get("n")
                
            lemma_idx += 1
            continue
    return d


def save_csv(data, filename):
    fieldnames = ["lemma_id", "lemma", "sense_num", "page_num", "type", "orthography", "pos", "etymology", "entry", "entry_str"]
    rows = [{
        "lemma_id": ent["lemma_id"],
        "lemma": ent["lemma"], 
        "sense_num": ent["sense_num"],
        "page_num": ent["page_num"],
        "type": ent["type"],
        "orthography": ent["orth"], 
        "pos": ent["pos"],
        "etymology": ent["etym"],
        "entry": ent["entry"],
        "entry_str": ent["entry_plain"]
        } for ent in data]
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(rows)  # Write data rows


if __name__ == "__main__":
    startTime = time()
    entries = get_entries("lewis-short.xml")
    save_csv(entries, "lewis-short-new.csv")
    print("Initial parsing completed.")
    add_cltk_data_csv("lewis-short-new.csv", "lewis-short-add.csv")
    print("CLTK data added.")
    merge_senses("lewis-short-add.csv", "lewis-short-merged.csv", "lewis-short-need-merging.txt")
    print("Duplicate lemmas merged.")
    print("Runtime:", time() - startTime, "s")
