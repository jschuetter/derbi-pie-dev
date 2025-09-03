"""

"""
import codecs

from bs4 import BeautifulSoup
from lxml import etree
from yaml import dump


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


def save_yaml(data, filename):
    with open(filename, "w") as f:
        dump(data, f)


if __name__ == "__main__":
    entries = get_entries("lewis.xml")
    save_yaml(entries, "lewis.yaml")
