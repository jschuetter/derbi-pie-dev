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


def get_entries(filename):
    root = get_root(filename)
    lemmata = set()
    d = {}
    for entry in root.findall(".//entry"):
        lemma = entry.get("key", "")
        entry_bs = BeautifulSoup(etree.tostring(entry), features="lxml")
        d[lemma] = entry_bs.text.strip()
        lemmata.add(lemma)
    return d


def save_csv(data, filename):
    fieldnames = ["lemma", "entry"]
    rows = [{"lemma": k, "entry": v} for k, v in data.items()]
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(rows)  # Write data rows


if __name__ == "__main__":
    entries = get_entries("lewis.xml")
    save_csv(entries, "lewis.csv")
