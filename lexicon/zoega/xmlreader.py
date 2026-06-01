"""
xmlreader.py
XML parser script for Zoega's Old Norse lexicon
"""

from lxml import etree
import csv, re
from time import time

from lexdata import *

XSLT_DOC = "./zoega-template.xslt"
SQL_NULL = "\\N"

def remove_tag(element, remove_empty_parent = True): 
    '''
    Remove a single element from the tree
    Default behavior also removes parent if the specified
    element was the only one in the node
    '''
    # Remove tag
    parent = element.getparent()
    parent.remove(element)

    # If parent is empty, remove it too
    if (
        remove_empty_parent and 
        len(parent) == 0 and 
        (not parent.text or 
        parent.text.strip() == '')
    ): 
        parent.getparent().remove(parent)

def get_entries(filename): 
    '''
    Return a dict of entries from the provided
    XML file
    '''
    parser = etree.XMLParser(load_dtd=True, no_network=False)
    tree = etree.parse(filename, parser=parser)
    root = tree.getroot()

    # Zoega dictionary XML does not include the following fields: 
    # page_num, orthography, components, stem, etymology

    # Lang code, editor, updated date fields will be filled in when
    # importing to MySQL

    dict_entries = []
    xslt_tree = etree.parse(XSLT_DOC)
    xslt = etree.XSLT(xslt_tree)
    lemma_idx = 1 # Start indexing at 1 to match SQL convention
    for xml_entry in root.findall(".//entry"): 
        try:
            lemma = xml_entry.get("word")
            # Remove hyphens from lemma (if present) for transcription
            ipa = ipa_oldnorse(lemma.replace("-", ""))

            # Split entry if multiple definitions
            # Def'n delimited by `<m1><b>I)</b></m1>` 
            # (followed by 'II)', 'III)', etc.)

            # List of definitions
            # Each element contains list of tags belonging to that definition
            defn_delimiters = xml_entry.findall('.//m1[b]')
            for delim in defn_delimiters:
                delim_text = "".join(delim.find("./b").itertext())
                # Remove delimiters that do not define separate definitions
                # (can't use contains() filter in lxml findall() method)
                if not ("I)" in delim_text or "V)" in delim_text): 
                    defn_delimiters.remove(delim)
                
            # Use delimiters to split definitions
            entry_definitions = []
            if len(defn_delimiters) <= 1: 
                # If 1 delimiter or less, process entire entry as one definition
                entry_definitions.append(list(xml_entry))
            else: 
                # Multiple definitions
                defn_idx = 0
                while defn_idx < len(defn_delimiters)-1: 
                    prev_idx = xml_entry.index(defn_delimiters[defn_idx])
                    next_idx = xml_entry.index(defn_delimiters[defn_idx+1])
                    entry_definitions.append(
                        xml_entry[prev_idx:next_idx]
                    )
                    defn_idx += 1
                # Append last definition
                entry_definitions.append(
                    xml_entry[xml_entry.index(defn_delimiters[defn_idx]):]
                )

            # Process each definition separately
            for entry_idx in range(len(entry_definitions)): 
                # Create temporary subentry object to hold elements of a single definition
                defn = etree.Element("subentry")
                defn.extend(entry_definitions[entry_idx])
                # Remove delimiter tags
                delim_tags = defn.findall(".//b")
                for dt in delim_tags: 
                    if "I)" in dt.text or "V)" in dt.text: 
                        remove_tag(dt)

                defn_num = ""
                if len(entry_definitions) > 1: 
                    # Format entry number to match Lewis-Short format
                    # (use brackets for multiple definitions)
                    defn_num = f"[{entry_idx+1}]" 

                new_entry = {
                    "lemma_id": str(lemma_idx),
                    "lemma": lemma,
                    "sense_num": defn_num,
                    "type": "main",  # Main definition
                    "ipa": ipa,
                    "pos": "",
                    "gender": "",
                    "entry": "",
                    "entry_str": "",  # Plaintext of entry (without HTML tags)
                    "gloss": "",
                }

                # Get POS or gender, as applicable
                # Test each <p> tag in entry; select first applicable
                p_tags = defn.findall(".//p")
                pos_tags = [
                    "m.", "f.", "n.", 
                    "v.", "v. refl.",
                    "a.", "adj.", "adv.", 
                    "pp.", "prep.", "interj."
                    ]

                for p_tag in p_tags:
                    if p_tag.text not in pos_tags: 
                        # Ignore; not desired data
                        continue
                    elif p_tag.text in ["m.", "f.", "n."]: 
                        # POS is noun, represented by gender
                        new_entry["gender"] = p_tag.text
                        new_entry["pos"] = "n."
                        # Remove tag
                        remove_tag(p_tag)
                        break
                    elif p_tag.text == "a.": 
                        # Normalize 'a.' notation to 'adj.'
                        new_entry["pos"] = "adj."
                        # Remove tag
                        remove_tag(p_tag)
                        break
                    else: 
                        # Other tags: adj., adv., pp., prep., interj.
                        new_entry["pos"] = p_tag.text
                        # Remove tag
                        remove_tag(p_tag)
                        break

                # Get entry gloss
                # Find first <trn> tag in entry, or (if not present) use entire first tag
                trn_tag = defn.find(".//trn")
                if trn_tag is not None: 
                    new_entry["gloss"] = trn_tag.text
                elif len(defn) >= 1: 
                    new_entry["gloss"] = "".join(defn[0].itertext())
                else: 
                    new_entry["gloss"] = "".join(defn.itertext())

                # Get entry senses
                # Use regex to recognize sense delimiter
                # Process tags one-by-one; check iteratively for senses
                senses = []
                current_sense = []
                for child in defn: 
                    # Check for sense delimiter
                    # Indent tags: m1 - m5
                    # Possible delimiters: I. - V., 1) - 17), A. with... | B. with...
                    if (
                        child.text is not None and 
                        re.match(r'm[1-5]', child.tag) and 
                        re.match(r'[AB]\. with |I?I?[IV]\. |1?[0-9]\) ', child.text)
                    ): 
                        if len(current_sense) > 0: 
                            new_sense_element = etree.Element("sense")
                            new_sense_element.extend(current_sense)
                            senses.append(new_sense_element)

                        current_sense = [child]
                    else: 
                        current_sense.append(child)
                if len(current_sense) > 0: 
                    new_sense_element = etree.Element("sense")
                    new_sense_element.extend(current_sense)
                    senses.append(new_sense_element)

                # Create sense subentries
                sense_num = []
                if defn_num: 
                    sense_num.append(defn_num)
                new_subentries = []
                for sense_tag in senses: 
                    # Check for sense delimiters in first child element
                    delim_match = None
                    if sense_tag[0].text is not None: 
                        delim_match = re.match(r'I?I?[IV]\.|[AB]\.|1?[0-9]\)', sense_tag[0].text)

                    if delim_match is None: 
                        # No delimiter, part of main sense
                        # Fill in main entry details here

                        # Pass sense contents to XSLT
                        # Append plaintext to entry_str
                        if new_entry["entry_str"] != "": 
                            raise Exception(f"Main entry field of entry {lemma} was not empty!\nContents:{new_entry["entry_str"]}")
                        new_entry["entry_str"] = re.sub(r'\n+\t?', "\\\\n", "".join(sense_tag.itertext()).rstrip())  # Plaintext of entry (without XML tags)
                        new_entry["entry"] = xslt(sense_tag, base_indent=etree.XSLT.strparam(str(1))).__str__().rstrip().replace(">\n<", "><").replace("\n", "\\n")

                    else: 
                        # Delimiter found; sub-sense entry
                        sense_delim = delim_match.group(0)
                        # Remove delimiter from tag text
                        sense_tag[0].text = sense_tag[0].text.replace(f"{sense_delim} ", "")
                        sense_lvl = int(sense_tag[0].tag[-1])
                        
                        if len(sense_num) > sense_lvl:
                            sense_num = sense_num[:sense_lvl]

                        while len(sense_num) < sense_lvl: 
                            sense_num.append("X")
                        sense_num[sense_lvl-1] = sense_delim.rstrip(".)")

                        # IPA, POS, gender, gloss left blank on sense entries
                        # (already encoded on main entry)
                        new_sense = {
                            "lemma_id": str(lemma_idx),
                            "lemma": lemma,
                            "sense_num": ".".join(sense_num),
                            "type": "sense",  # Sense subentry
                            "ipa": "",
                            "pos": "",
                            "gender": "",
                            "entry_str": re.sub(r'\n+\t?', "\\\\n", "".join(sense_tag.itertext()).rstrip()),  # Plaintext of entry (without XML tags)
                            "entry": xslt(sense_tag, base_indent=etree.XSLT.strparam(str(sense_lvl))).__str__().rstrip().replace(">\n<", "><").replace("\n", "\\n"),
                            "gloss": "",
                        }
                        new_subentries.append(new_sense)

                # Convert first sense to main entry, if still blank
                if new_subentries and new_entry["entry"] == "":
                    first_sense = new_subentries.pop(0)
                    new_entry["entry_str"] = first_sense["entry_str"]
                    new_entry["entry"] = first_sense["entry"]

                # TODO: create gloss 
                # (concatenate senses or just use first?)

                # Final processing
                new_entries = [new_entry] + new_subentries
                for ne in new_entries: 
                    for k,v in ne.items():
                        # Convert empty fields to SQL_NULL
                        if v == "":
                            ne[k] = SQL_NULL
                        # TODO: copy punctuation/parentheses handling from 
                        # iterReader.py? (do we need this?)
                    dict_entries.append(ne)


        except AssertionError as ae: 
            print(f"Assertion failed in entry {lemma}")
        except Exception as e: 
            # lemma = xml_entry.get("entry")
            print(f"Exception in entry {lemma}: {e}")
            raise e
        finally: 
            lemma_idx += 1
            continue
        
    return dict_entries

def save_csv(data, filename):
    fieldnames = ["lemma_id", "lemma", "sense_num", "type", "ipa", "pos", "gender", "entry", "entry_str", "gloss"]
    rows = [{
        "lemma_id": ent["lemma_id"],
        "lemma": ent["lemma"], 
        "sense_num": ent["sense_num"],
        "type": ent["type"],
        "ipa": ent["ipa"], 
        "pos": ent["pos"],
        "gender": ent["gender"],
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
    entries = get_entries("zoega.xml")
    save_csv(entries, "zoega.csv")
    print("Parsing completed.")
    print("Runtime:", time() - startTime, "s")
