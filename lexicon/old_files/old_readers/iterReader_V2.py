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
                    if child.tag in ["orth", "itype"]:  # Add <bibl> tag to accepted list, see 'Aaron' - 22 Sep 2025
                    # if child.tag in ["itype"]:  # Add <bibl> tag to accepted list, see 'Aaron' - 22 Sep 2025
                        d[lemma]["orth"] += entry[idx-1].tail if entry[idx-1].tail else ""
                    else:
                        break
                    
                    d[lemma]["orth"] += "".join(child.itertext())
                    idx += 1
                
                # Handle case where no other tags follow orth
                if idx >= len(entry):
                    if child.tail:
                        d[lemma]["entry"] += child.tail.lstrip(":., ").rstrip()

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
                if etymTags is not None: 
                    d[lemma]["etym"] = "".join(etymTags[0].itertext())
                else: 
                    d[lemma]["etym"] = sqlNull
            elif len(etymTags) > 1: 
                print("etymTags:", len(etymTags))
                for t in etymTags:
                    print(t.tag, t.text)
                raise ValueError(f"Entry {lemma} has multiple <etym> tags")
            else: 
                # Parse entire contents of <etym> tag, including any <foreign> tags
                d[lemma]["etym"] = "".join(etymTags[0].itertext())


            child = entry[idx]
            while child.tag in ["gen", "pos", "etym"]:
                # Ignore tag contents, parsed above
                # If <etym> is preceded by another tag (cf. 'abaculus'), parse in definition
                idx += 1
                # Handle case where no other tags follow
                if idx >= len(entry):
                    if child.tail:
                        d[lemma]["entry"] += (child.tail if child.tail else "").lstrip(":., ")
                        d[lemma]["entryPlain"] += (child.tail if child.tail else "").lstrip(":., ")

                child = entry[idx]
            
            # Append tail of previous tag
            prev = entry[idx-1]
            d[lemma]["entry"] += (prev.tail if prev.tail else "").lstrip(":., ")
            d[lemma]["entryPlain"] += (prev.tail if prev.tail else "").lstrip(":., ")

            # Etymology
            # if child.tag == "etym":
            #     # Ignore tag contents if in order, parsed above
            #     # If out-of-order (e.g. if includes <lbl> tag - cf 'abaculus'), 
            #     # Include in definition

            #     # Parse entire contents of <etym> tag, including any <foreign> tags
            #     # d[lemma]["etym"] = "".join(child.itertext())
            #     # Append tail to entry definition
            #     d[lemma]["entry"] += (child.tail if child.tail else "").lstrip(":., ").rstrip()
            #     d[lemma]["entryPlain"] += (child.tail if child.tail else "").lstrip(":., ").rstrip()
            #     idx += 1

            # Parse remaining text in XML format as definition
            # N.B. quotes will be encoded in CSV doubled ( " --> "" )
            while idx < len(entry):
                child = entry[idx]
                # Remove listed tags - ??
                if child.tag in ["foreign", "lbl", "etym"]:
                    d[lemma]["entry"] += "".join(child.itertext())
                    if child.tail: 
                        d[lemma]["entry"] += child.tail
                else: 
                    d[lemma]["entry"] += etree.tostring(child, encoding="unicode", with_tail=True) #, pretty_print=True) <-- messes up CSV formatting?
                d[lemma]["entryPlain"] += "".join(child.itertext())
                if child.tail: 
                    d[lemma]["entryPlain"] += child.tail
                idx += 1
        except IndexError as e: 
            # Continue to next entry if end of entry is reached
            if lemma in ["alienigena", "alicubi", "Alii", "alienigenus"]:
                print("IndexError at entry", lemma)
            pass
        except Exception as e:
            print(f"Exception at entry {lemma}")
            print(e)
        finally:
            for k,v in d[lemma].items():
                if v == "": 
                    d[lemma][k] = sqlNull
                else: 
                    d[lemma][k] = v.strip(", ").lstrip(".") # Clean up leading/trailing punctuation
                    # Close unclosed parentheses
                    openParens = d[lemma][k].count("(")
                    closeParens = d[lemma][k].count(")")
                    if openParens > closeParens:
                        d[lemma][k] += ")" * (openParens - closeParens)
                    elif closeParens > openParens:
                        d[lemma][k] = "(" * (closeParens - openParens) + d[lemma][k]
            continue
    # print(d["abjunctus"]) # Example entry
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
    entries = get_entries("lewis-short.xml")
    save_csv(entries, "lewis-short.csv")
