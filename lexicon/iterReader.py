"""
iterReader.py
Modified version of CLTK Lewis Latin lexicon XML reader to convert to CSV
Original source: https://github.com/cltk/cltk_lat_lewis_elementary_lexicon/
"""
# import codecs

from lxml import etree
import csv
from time import time

def get_root(filename):
    parser = etree.XMLParser(load_dtd=True, no_network=False)
    tree = etree.parse(filename, parser=parser)
    return tree.getroot()

def get_entries(filename):
    root = get_root(filename)
    lemmata = set()
    d = []
    sqlNull = "\\N"
    entry_idx = 0
    lemma_idx = 0
    for xml_entry in root.findall(".//entryFree"):
        try:
            # print("Entry:", entry)
            lemma = xml_entry.get("key", "")
            new_entry = {
                "entry_id": str(entry_idx),
                "lemma_id": str(lemma_idx),
                "lemma": lemma,
                "parent_id": "",
                "child_ids": "",
                "type": "",
                "orth": "",
                "pos": "",
                "etym": "",
                "entry": "",
                "entryPlain": ""  # Plaintext of entry (without XML tags)
            }

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
                        new_entry["entryPlain"] += child.tail.lstrip("., ").rstrip()
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
            new_entry["entryPlain"] += (child.tail if child.tail else "").lstrip("., ").rstrip()

            # Parse remaining text in XML format as definition
            # N.B. quotes will be encoded in CSV doubled ( " --> "" )
            while idx < len(xml_entry):
                child = xml_entry[idx]
                # Remove <foreign> tags - ??
                if child.tag == "foreign":
                    new_entry["entry"] += "".join(child.itertext())
                    if child.tail: 
                        new_entry["entry"] += child.tail
                else: 
                    new_entry["entry"] += etree.tostring(child, encoding="unicode", with_tail=True) #, pretty_print=True) <-- messes up CSV formatting?
                new_entry["entryPlain"] += "".join(child.itertext())
                if child.tail: 
                    new_entry["entryPlain"] += child.tail
                idx += 1
                
        except IndexError as ie:
            print(f"IndexError in entry {lemma}: {ie}")
            pass
        except Exception as e: 
            print(f"Exception in entry {lemma}\n{e}")
        finally:
            # Continue to next entry if end of entry is reached
            for k,v in new_entry.items():
                if v == "": 
                    new_entry[k] = sqlNull
                else: 
                    new_entry[k] = v.strip(" ,").lstrip(".") # Clean up leading/trailing punctuation
                    # Close unclosed parentheses
                    openParens = new_entry[k].count("(")
                    closeParens = new_entry[k].count(")")
                    if openParens > closeParens:
                        new_entry[k] += ")" * (openParens - closeParens)
                    elif closeParens > openParens:
                        new_entry[k] = "(" * (closeParens - openParens) + new_entry[k]
            d.append(new_entry)
            entry_idx += 1
            lemma_idx += 1
            continue
    return d


def save_csv(data, filename):
    fieldnames = ["entry_id", "lemma_id", "lemma", "parent_id", "child_ids", "type", "orthography", "pos", "etymology", "entry"]
    rows = [{
        "entry_id": ent["entry_id"],
        "lemma_id": ent["lemma_id"],
        "lemma": ent["lemma"], 
        "parent_id": ent["parent_id"],
        "child_ids": ent["child_ids"],
        "type": ent["type"],
        "orthography": ent["orth"], 
        "pos": ent["pos"],
        "etymology": ent["etym"],
        "entry": ent["entry"]
        } for ent in data]
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(rows)  # Write data rows


if __name__ == "__main__":
    startTime = time()
    entries = get_entries("lewis-short.xml")
    save_csv(entries, "lewis-short-2.csv")
    print("Runtime:", time() - startTime, "s")
