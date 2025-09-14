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

def getProp(entry, tag):
    '''Get text content of first matching tag in entry, or sql NULL if not found'''
    sqlNull = "\\N"
    el = entry.find(f".//{tag}")
    return el.text if el is not None and el.text else sqlNull

def get_entries(filename):
    root = get_root(filename)
    lemmata = set()
    d = {}
    sqlNull = "\\N"
    ex = root.find(".//entryFree[@key='abalieno']")
    for child in ex:
        walk = lambda c: [c.tag, c.text, [[walk(g), g.tail] for g in c] if len(c) else '']
        print(walk(child))
    # print("Senses:")
    # for sense in ex.findall(".//sense"):
    #     print(''.join(sense.itertext()).strip())
    # print([s.text_content() for s in ex.findall(".//sense")])
        # print(child.tag, child.text)
    for entry in root.findall(".//entryFree"):
        # print("Entry:", entry)
        lemma = entry.get("key", "")
        # entry_bs = BeautifulSoup(etree.tostring(entry), features="lxml")
        # d[lemma] = entry_bs.text.strip()
        d[lemma] = {
            "orth": " or ".join(o.text for o in entry.findall(".//orth")),
            "itype": getProp(entry, "itype"),
            "gen": getProp(entry, "gen"),
            "pos": getProp(entry, "pos"),
            "etym": getProp(entry, "etym"),
            "entry": ' | '.join([''.join(sense.itertext()).strip() for sense in entry.findall(".//sense")])
        }
        lemmata.add(lemma)
    print(d["abalieno"]) # Example entry
    return d


def save_csv(data, filename):
    fieldnames = ["lemma", "orthography", "principal parts", "gender", "part-of-speech", "etymology", "entry"]
    rows = [{
        "lemma": k, 
        "orthography": v["orth"], 
        "principal parts": v["itype"], 
        "gender": v["gen"],
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
