"""
readerMod.py
Modified version of CLTK Lewis Latin lexicon XML reader to convert to CSV
Original source: https://github.com/cltk/cltk_lat_lewis_elementary_lexicon/
"""
# import codecs

from bs4 import BeautifulSoup
from lxml import etree
import csv

def get_root(filename):
    parser = etree.XMLParser(load_dtd=True, no_network=False)
    tree = etree.parse(filename, parser=parser)
    return tree.getroot()

def getProp(entry, initTag: str, acceptedTags: list) -> str:
    '''
    Get text content of entry starting at first instance of tag, through instances of accepted tags
    '''
    sqlNull = "\\N"

    child = entry.find(f".//{tag}")
    if child is None:
        return sqlNull

    idx = entry.index(startTag) # Index to start parsing at
    outputStr = (child.text if child.text else "")
    while idx < len(entry):
        child = entry[idx]
        if child.tag in acceptedTags: 
            outputStr += child.tail if child.tail else ""
        else:
            return outputStr if outputStr else sqlNull
        
        # Child is in accepted tags, append text & tail, continue loop
        outputStr += (child.text if child.text else "")
        idx += 1

def get_entries(filename):
    root = get_root(filename)
    lemmata = set()
    d = {}
    sqlNull = "\\N"
    # ex = root.find(".//entryFree[@key='abalieno']")
    # for child in ex:
    #     walk = lambda c: [c.tag, c.text, [[walk(g), g.tail] for g in c] if len(c) else '']
    #     print(walk(child))
    # print("Senses:")
    # for sense in ex.findall(".//sense"):
    #     print(''.join(sense.itertext()).strip())
    # print([s.text_content() for s in ex.findall(".//sense")])
    #     print(child.tag, child.text)
    for entry in root.findall(".//entryFree"):
        try:
            # print("Entry:", entry)
            lemma = entry.get("key", "")
            d[lemma] = {
                "type": "",
                "orth": "",
                "pos": "",
                "etym": "",
                "entry": ""
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
                    if child.tag in ["orth", "itype"]: 
                        d[lemma]["orth"] += child.tail if child.tail else ""
                    else:
                        break
                    
                    # Child is in accepted tags, append text & tail, continue loop
                    d[lemma]["orth"] += (child.text if child.text else "")
                    idx += 1
                
                # Handle case where no other tags follow orth
                if idx >= len(entry):
                    if child.tail:
                        d[lemma]["entry"] += child.tail.lstrip(", ").rstrip()
            else: 
                d[lemma]["orth"] = sqlNull

            # Gender OR pos -- should only be 1?
            if child.tag in ["gen", "pos"]:
                if child.tag == "gen": 
                    d[lemma]["pos"] += "n. "
                d[lemma]["pos"] += (child.text if child.text else "")
                idx += 1
                # If next tag is etym, parse it in its own category
                # Else, add tail to definition, removing leading commas & spaces
                if entry[idx].tag == "etym": 
                    child = entry[idx]
                    d[lemma]["etym"] = (child.text if child.text else sqlNull)
                    idx += 1
                else: 
                    d[lemma]["etym"] = sqlNull
                    d[lemma]["entry"] += (child.tail if child.tail else "").lstrip(", ").rstrip()
            else: 
                d[lemma]["pos"] = sqlNull
                if child.tag == "etym":
                    d[lemma]["etym"] = (child.text if child.text else sqlNull)
                    d[lemma]["entry"] += (child.tail if child.tail else "").lstrip(", ").rstrip()
                    idx += 1
                else:
                    d[lemma]["etym"] = sqlNull

            # Parse remaining text in XML format as definition
            # N.B. quotes will be encoded in CSV doubled ( " --> "" )
            while idx < len(entry):
                child = entry[idx]
                d[lemma]["entry"] += etree.tostring(child, encoding="unicode", with_tail=True) #, pretty_print=True) <-- messes up CSV formatting?
                if child.tail: 
                    d[lemma]["entry"] += child.tail
                idx += len(child) + 1 # Skip all child tags (already parsed)
                
        except IndexError:
            # Continue to next entry if end of entry is reached
            for k,v in d[lemma].items():
                if v == "": d[lemma][k] = sqlNull
            continue
    print(d["abjunctus"]) # Example entry
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
    entries = get_entries("lewis-short-100.xml")
    save_csv(entries, "lewis-short-100.csv")
