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
    d = {}
    sqlNull = "\\N"
    for entry in root.findall(".//entryFree"):
        try:
            # print("Entry:", entry)
            lemma = entry.get("key", "")
            d[lemma] = {
                "type": "",
                "orth": "",
                "pos": "",
                "etym": "",
                "entry": "",
                "entryPlain": ""  # Plaintext of entry (without XML tags)
            }

            # Use XPath to parse entry type
            d[lemma]["type"] = entry.get("type", "")


            # Iterate through all tags in entry, parse appropriate data
            idx = 0
            child = entry[idx]
            # Orthography + principal parts
            if child.tag == "orth":
                d[lemma]["orth"] += (child.text if child.text else "")
                idx += 1
                while idx < len(entry):
                    child = entry[idx]
                    # Child is in accepted tags, append text & preceding tail, continue loop
                    if child.tag in ["orth", "itype", "bibl"]:  # Add <bibl> tag to accepted list, see 'Aaron' - 22 Sep 2025
                        d[lemma]["orth"] += entry[idx-1].tail if entry[idx-1].tail else ""
                    else:
                        break
                    
                    d[lemma]["orth"] += "".join(child.itertext())
                    idx += 1
                
                # Handle case where no other tags follow orth
                if idx >= len(entry):
                    if child.tail:
                        d[lemma]["entry"] += child.tail.lstrip("., ").rstrip()
                        d[lemma]["entryPlain"] += child.tail.lstrip("., ").rstrip()
                    continue  # Move to next entry
                    
            else: 
                d[lemma]["orth"] = sqlNull

            # Gender OR pos -- should only be 1?
            # Parse from tag contents only
            genTag = entry.find("gen")
            posTag = entry.find("pos")
            if genTag is not None and posTag is not None: 
                # raise ValueError(f"Entry {lemma} has both <gen> and <pos> tags")
                # Take first chronologically
                if entry.index(genTag) < entry.index(posTag):   
                    d[lemma]["pos"] = "n. " + (genTag.text if genTag.text else "")
                else: 
                    d[lemma]["pos"] = (posTag.text if posTag.text else "")
            else: 
                if genTag is None and posTag is None: 
                    # If not found, search descendants
                    genTag = entry.find(".//gen")
                    posTag = entry.find(".//pos")

                if genTag is not None: 
                    d[lemma]["pos"] = "n. " + (genTag.text if genTag.text else "")
                elif posTag is not None: 
                    d[lemma]["pos"] = (posTag.text if posTag.text else "")
                else: 
                    # If still not found, set to Null
                    d[lemma]["pos"] = sqlNull

            # Parse etym tag -- should only be 1
            etymTags = entry.findall("etym")
            if etymTags is None or len(etymTags) <= 0: 
                # If not found, check descendants
                etymTags = entry.findall(".//etym")
                if etymTags is not None and len(etymTags) >= 1: 
                    d[lemma]["etym"] = "".join(etymTags[0].itertext())
                else: 
                    d[lemma]["etym"] = sqlNull
            else: 
                # Take first tag only
                # Parse entire contents of <etym> tag, including any <foreign> tags
                d[lemma]["etym"] = "".join(etymTags[0].itertext())


            while idx < len(entry):
                child = entry[idx]
                if child.tag in ["gen", "pos", "etym"]:
                    # Ignore contents
                    idx += 1
                    continue
                else: 
                    break

            # Append tail to entry definition
            child = entry[idx-1]
            d[lemma]["entry"] += (child.tail if child.tail else "").lstrip("., ").rstrip()
            d[lemma]["entryPlain"] += (child.tail if child.tail else "").lstrip("., ").rstrip()

            # Parse remaining text in XML format as definition
            # N.B. quotes will be encoded in CSV doubled ( " --> "" )
            while idx < len(entry):
                child = entry[idx]
                # Remove <foreign> tags - ??
                if child.tag == "foreign":
                    d[lemma]["entry"] += "".join(child.itertext())
                    if child.tail: 
                        d[lemma]["entry"] += child.tail
                else: 
                    d[lemma]["entry"] += etree.tostring(child, encoding="unicode", with_tail=True) #, pretty_print=True) <-- messes up CSV formatting?
                d[lemma]["entryPlain"] += "".join(child.itertext())
                if child.tail: 
                    d[lemma]["entryPlain"] += child.tail
                idx += 1
                
        except IndexError as ie:
            print(f"IndexError in entry {lemma}: {ie}")
            pass
        except Exception as e: 
            print(f"Exception in entry {lemma}\n{e}")
        finally:
            # Continue to next entry if end of entry is reached
            for k,v in d[lemma].items():
                if v == "": 
                    d[lemma][k] = sqlNull
                else: 
                    d[lemma][k] = v.strip(" ,").lstrip(".") # Clean up leading/trailing punctuation
                    # Close unclosed parentheses
                    openParens = d[lemma][k].count("(")
                    closeParens = d[lemma][k].count(")")
                    if openParens > closeParens:
                        d[lemma][k] += ")" * (openParens - closeParens)
                    elif closeParens > openParens:
                        d[lemma][k] = "(" * (closeParens - openParens) + d[lemma][k]
            continue
    return d


def save_csv(data, filename):
    fieldnames = ["lemma", "type", "orthography", "part-of-speech", "etymology", "entry"]
    rows = [{
        "lemma": k, 
        "type": v["type"],
        "orthography": v["orth"], 
        "part-of-speech": v["pos"],
        "etymology": v["etym"],
        "entry": v["entry"]
        } for k, v in data.items()]
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(rows)  # Write data rows


if __name__ == "__main__":
    startTime = time()
    entries = get_entries("lewis-short.xml")
    save_csv(entries, "lewis-short-2.csv")
    print("Runtime:", time() - startTime, "s")
