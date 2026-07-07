"""
xmlreader.py
Modified version of CLTK Lewis Latin lexicon XML reader to convert to CSV
Original source: https://github.com/cltk/cltk_lat_lewis_elementary_lexicon/
"""
# import codecs

from lxml import etree, html
import csv, re
from time import time
from copy import deepcopy
from lexdata import *

DIGITS_STR = "0123456789"
XSLT_DOC = "./lsj-template.xslt"

def get_root(filename):
    parser = etree.XMLParser(load_dtd=True, no_network=False)
    tree = etree.parse(filename, parser=parser)
    return tree.getroot()

def comes_before(root, a, b):
    '''
    Helper method for determining whether Element
    `a` comes before Element `b` in document order.
    Searches only subtree under Element `root`.
    Returns `True` if `b` is None or not found 
    in `root`'s subtree.

    :returns: bool
    '''
    if a is None: 
        return False
    if b is None: 
        return True
    
    found_a = False
    for el in root.iterdescendants():
        if el is a:
            found_a = True
        if el is b:
            return found_a
    return False  # if b not found (or either not in subtree)

def normalize_punct(input_str):
    '''
    Regexp helper function for normalizing spacing around punctuation
    '''
    fix_space_before = re.sub(r' ([,.;:\]\)])', '\\g<1>', input_str)
    fix_space_after = re.sub(r'([\(\[]) ', '\\g<1>', fix_space_before)
    fix_missing_after = re.sub(r'([,;:])(?! )', '\\g<1> ', fix_space_after)
    fix_missing_between = re.sub(r'([)\]])([(\[])', '\\g<1> \\g<2>', fix_missing_after)
    normalize_space = re.sub(r' +', ' ', fix_missing_between)
    return normalize_space

def get_entries(filename):
    root = get_root(filename)
    d = []
    sqlNull = "\\N"
    xslt_tree = etree.parse(XSLT_DOC)
    xslt = etree.XSLT(xslt_tree)
    # Start indexes at 1 to match SQL convention
    lemma_idx = 1
    sense_idx = 1
    cur_page = 1  # Current page number
    for xml_entry in root.findall(".//entryFree"):
        try:
            lemma_id = int(xml_entry.get("id").lstrip("n")) + 1  # Add 1 to unify with previous convention
            key1 = xml_entry.get("key")
            # Pull lemma from initial orthography tag, if present
            if xml_entry[0].tag == "orth":
                lemma = xml_entry[0].text
                lemma = lemma.strip(' ,.;:') # Strip punctuation
            else: 
                # Fallback to key1 if orth not found
                lemma = re.sub(r'[0-9]+$', '', key1)
                is_affix = False
            lemma_normal = xml_entry.get("key3", "")
            new_entry = {
                "lemma_id": str(lemma_id),
                "lemma": lemma,
                "lemma_normalized": lemma_normal,
                "lemma_translit": greek_to_roman(lemma_normal),
                "sense_num": re.match(r'[0-9]+$', key1) or "",
                "page_num": str(cur_page),
                "type": xml_entry.get("type", ""),
                "ipa": ipa_greek(lemma),
                "orth": "",
                "pos": "",
                "gender": "",
                "etym": "",
                "entry": etree.Element("entry"),  # Empty XML element for storing elements (to be passed to XSLT later)
                "entry_str": "",  # Plaintext of entry (without XML tags)
                "gloss": "",
                "entry_type": "combining_form" if is_affix else "",
                # Senses only
                "sense_id": "",
                "h_number": "",
                "parent_h_number": ""
            }
            new_subentries = []    # Initialize this here to avoid double-adding subentries if exception triggered

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
                    if child.tag in ["orth", "itype", "pron"]:  # Add <bibl> tag to accepted list, see 'Aaron' - 22 Sep 2025
                        new_entry["orth"] += xml_entry[idx-1].tail if xml_entry[idx-1].tail else ""
                    else:
                        break
                    
                    new_entry["orth"] += " " + "".join(child.itertext())
                    idx += 1
                
                # Parse out newlines + indent spacing
                new_entry["orth"] = re.sub(r'\n +', ' ', new_entry["orth"])

                # Handle case where no other tags follow orth
                if idx >= len(xml_entry):
                    if child.tail:
                        new_entry["entry"] = child.tail
                        new_entry["entry_str"] = child.tail
                    raise StopIteration  # Move to next entry
                    
            else: 
                new_entry["orth"] = sqlNull

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

            
            # Parse gender tag, if present
            # N.B. <pos> tags used only for partic. citations
            genTag = xml_entry.find(".//gen")
            if genTag is not None:
                # Check to make sure <gen> does not belong to later sense
                gen_p = genTag.getparent()
                if ( gen_p.tag != "sense" or 
                    gen_p.tag == "sense" and gen_p.get("id") == xml_entry.get("id") + ".0" ):
                        # Convert article to gender
                        if genTag.text in ("ὁ", "οἱ"):
                            new_entry["gender"] = "m."
                            new_entry["pos"] = "n."
                        elif genTag.text in ("ἡ", "αἱ"):
                            new_entry["gender"] = "f."
                            new_entry["pos"] = "n."
                        elif genTag.text in ("τό", "τά"):
                            new_entry["gender"] = "n."
                            new_entry["pos"] = "n."
                        else: 
                            print("Bad gender")
                            raise ValueError(f"Unexpected gender value in lemma {lemma}: {genTag.text}")

            # while idx < len(xml_entry):
            #     child = xml_entry[idx]
            #     if child.tag in ["gen", "pos", "etym"]:
            #         # Ignore contents
            #         idx += 1
            #         continue
            #     else: 
            #         break

            # Append tail to entry definition
            child = xml_entry[idx-1]
            entry_pfx = (child.tail or "")

            # Parse tags up to next <sense> as entry
            sense_tags = xml_entry.findall(".//sense")
            second_sense_idx = xml_entry.index(sense_tags[1]) if len(sense_tags) > 1 else None
            while idx < (second_sense_idx or len(xml_entry)):
                new_entry["entry"].append(deepcopy(xml_entry[idx]))
                idx += 1

            # Process entry field in XSLT, 
            # remove newlines between tags,
            # and escape in-text newlines
            entry_html = xslt(new_entry["entry"]).__str__().rstrip()

            new_entry["entry"] = entry_pfx + entry_html
            # Normalize punctuation & spacing
            new_entry["entry"] = normalize_punct(new_entry["entry"])
            # Convert HTML to plaintext
            e_html_obj = html.fromstring(new_entry["entry"])
            new_entry["entry_str"] = html.tostring(e_html_obj, method="text", encoding="unicode")

            # Parse gloss
            # Find first <tr> tag (before sub-senses),
            # then capture all text contents,
            # plus any text in-between or contained
            # by consecutive <tr> tags
            # (excl. tails on either side)
            first_tr = xml_entry.find(".//tr")
            if ( first_tr is not None and 
                comes_before(xml_entry, first_tr, 
                             sense_tags[1] if len(sense_tags) > 1 else None)
            ): 
                tr_p = first_tr.getparent()
                tr_idx = tr_p.index(first_tr)

                new_entry["gloss"] += first_tr.text or ""

                # Capture consecutive <tr> tags
                next_tr = tr_p[tr_idx+1] if tr_idx < len(tr_p) - 1 else None
                while next_tr is not None and next_tr.tag == "tr":
                    new_entry["gloss"] += f" {first_tr.tail}" or ""
                    new_entry["gloss"] += f" {next_tr.text}" or ""
                    first_tr = next_tr
                    tr_idx += 1
                    next_tr = tr_p[tr_idx+1] if tr_idx < len(tr_p) - 1 else None

                # Fix spacing & punctuation
                new_entry["gloss"] = normalize_punct(new_entry["gloss"].strip(" \n.,;:"))
                

            # Get all sense tags as sub-entries
            parent_ids = [None, f"{xml_entry.get("id")}.0"]  # List of parent IDs by level -- [0] is None by convention
            # All common fields are Null
            for sense_tag in sense_tags[1:]:
                # Get parent id
                sense_lvl = int(sense_tag.get("level"))
                sense_id = sense_tag.get("id", "")
                while sense_lvl >= len(parent_ids):
                    parent_ids.append(None)
                parent_ids[sense_lvl] = sense_id
                parent_id = ""
                if sense_lvl > 1: 
                    parent_lvl = sense_lvl - 1
                    while parent_lvl > 0 and parent_ids[parent_lvl] is None: 
                        parent_lvl -= 1
                    if parent_lvl > 0: 
                        parent_id = parent_ids[parent_lvl]

                parent_lvl = sense_lvl - 1 if sense_lvl >= 2 else None

                new_subentry = {
                    "lemma_id": str(lemma_id),
                    "lemma": new_entry["lemma"],
                    "lemma_normalized": "",
                    "lemma_translit": "",
                    "sense_num": sense_tag.get("n", ""), # Initialized below
                    "page_num": str(cur_page),
                    "type": "sense",
                    "ipa": sqlNull,
                    "orth": sqlNull,
                    "pos": sqlNull,
                    "gender": sqlNull,
                    "etym": sqlNull,
                    "entry": "",  # Processing done below
                    "entry_str": "",  # Plaintext of entry (without XML tags)
                    "entry_type": "",
                    "gloss": "",  # Populated below
                    "sense_id": str(sense_idx),
                    "h_number": sense_id,
                    "parent_h_number": parent_id,
                }

                # Process subentry HTML
                subentry_html = xslt(sense_tag).__str__().rstrip()
                    
                # Normalize punctuation & spacing
                new_subentry["entry"] = normalize_punct(subentry_html)
                # Convert HTML to plaintext (ignore empty sense tags - see n13671.1)
                if subentry_html:
                    se_html_obj = html.fromstring(subentry_html)
                    new_subentry["entry_str"] = html.tostring(se_html_obj, method="text", encoding="unicode")


                # Parse gloss
                first_tr = sense_tag.find("tr")
                if first_tr is not None: 
                    tr_idx = sense_tag.index(first_tr)
                    new_subentry["gloss"] += f" {first_tr.text}" or ""

                    # Capture consecutive <tr> tags
                    next_tr = xml_entry[tr_idx+1] if tr_idx < len(xml_entry) - 1 else None
                    while next_tr is not None and next_tr.tag == "tr":
                        new_subentry["gloss"] += f" {first_tr.tail}" or ""
                        new_subentry["gloss"] += f" {next_tr.text}" or ""
                        first_tr = next_tr
                        tr_idx += 1
                        next_tr = xml_entry[tr_idx+1] if tr_idx < len(xml_entry) - 1 else None
                    
                    # Normalize punctuation & spacing
                    new_subentry["gloss"] = normalize_punct(new_subentry["gloss"].strip(" \n.,;:"))
                        

                # Add entry as child of parent
                new_subentries.append(new_subentry)

                # Check for page break in entry
                page_break_tag = sense_tag.findall(".//pb")
                if page_break_tag: 
                    # If found, update to highest page number seen
                    cur_page = page_break_tag[-1].get("n")
                
                sense_idx += 1
                
                
        except StopIteration:
            pass # Ignore
        # except IndexError as ie:
        #     print(f"IndexError in entry {lemma}: {ie}")
        # except Exception as e: 
        #     print(f"Exception in entry {lemma}\n{e}")
        finally:
            # Continue to next entry if end of entry is reached
            new_entries = [new_entry] + new_subentries
            for ne in new_entries: 
                for k,v in ne.items():
                    if v == "": 
                        ne[k] = sqlNull
                    else: 
                        ne[k] = v.strip(" ,:\n").lstrip(".)").rstrip("(") # Clean up leading/trailing punctuation
                        # Close unclosed parentheses
                        # openParens = ne[k].count("(")
                        # closeParens = ne[k].count(")")
                        # if openParens > closeParens:
                        #     ne[k] += ")" * (openParens - closeParens)
                        # elif closeParens > openParens:
                        #     ne[k] = "(" * (closeParens - openParens) + ne[k]
                d.append(ne)

            # Check for page break in entry
            # N.B. first updated when searching subentries - this may not do anything
            page_break_tag = xml_entry.findall(".//pb")
            if page_break_tag: 
                # If found, update to highest page number seen
                cur_page = page_break_tag[-1].get("n")
                
            lemma_idx += 1
    return d


def save_csv(data, filename):
    fieldnames = list(data[0].keys())
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()  # Write header row
        writer.writerows(data)  # Write data rows


if __name__ == "__main__":
    filename = 'grc.lsj.perseus-eng1'
    startTime = time()
    entries = get_entries(f"lex-src/{filename}.xml")
    save_csv(entries, f"{filename}.csv")
    print("Initial parsing completed.")
    print("Runtime:", time() - startTime, "s")
