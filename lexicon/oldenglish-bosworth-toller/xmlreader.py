'''
xmlreader.py
XML parser script for the Bosworth and Toller Old English dictionary
'''

import csv, re
from lxml import etree
from time import time
from copy import deepcopy
import traceback

import lexdata
from lexdata import ipa_oldenglish
from unescape import unescape

SQL_NULL = "\\N"
REMEDIATE_PATH = "remediate-entries.tsv"
# Global sense_idx variable to be used between instances of `parse_senses()`
sense_idx = 1
# Global list of entries to remediate, with messages
remediate_entries = []

def line_xml(raw_line, wrapper_tag = "xml_line"):
    '''
    Generates an lxml.etree.Element instance
    from a line of text which has XML syntax
    but is not wrapped in an XML tag.

    Optional argument wrapper_tag can be used
    to set the name of the wrapper element.

    Intended to help parse Bosworth-Toller line-by-line.
    '''
    xml_str = f"<{wrapper_tag}>{raw_line}</{wrapper_tag}>"
    try:
        elem = etree.XML(xml_str)
    except etree.XMLSyntaxError as e:
        print("XML SYNTAX ERROR")
        print(raw_line)
        raise e
    return elem

class EntryCompleted(Exception):
    '''Custom Exception to denote all XML in line has been parsed'''
    pass

class RemediateError(Exception):
    '''Custom Exception for documenting entries that need remediation'''
    def __init__(self, lemma, msg, type="ERROR"):
        super().__init__()
        self.lemma = lemma
        self.msg = msg
        self.type = type

def get_entries(filename):
    '''
    Return a dict of entries from the provided
    XML file
    '''
    global remediate_entries
    dict_entries = []
    page_num = None  # Page number counter
    prev_entry = None
    lemma_idx = 1 # Start indexing at 1 to match SQL convention

    with open(filename, 'r') as f: 
        for line in f: 
            # Strip trailing newline from line
            line = line.strip()
            
            if line == "": 
                # Ignore empty lines
                continue
            elif line.startswith("<HEADER>"): 
                # Ignore header tags
                continue
            elif line.startswith("<letterheader>"):
                # Ignore letterheader, following text
                prev_entry = None
                continue
            elif line.startswith("<PAGE NUM="):
                # Check for page tag (invalid XML - won't parse)
                # Extract page number for entries
                page_num = int(line[12:16])
                continue

            # Escape HTML characters
            line_unicode = unescape(line)
            line_elem = line_xml(line_unicode)

            if (
                # Check for initial text node or
                line_elem.text is not None or 
                # initial <I> tag => entry overflow or 
                line_elem[0].tag != "B" or
                ( 
                    # Sense delimiter tag => entry overflow
                    is_sense_delim(line_elem[0])
                )
            ):
                if prev_entry is None: 
                    # If no preceding data or follows letterheader, ignore
                    continue
                else: 
                    # Append data to previous entry
                    # If text-only, append to previous entry
                    if len(line_elem) == 0: 
                        if prev_sense is not None:
                            if prev_sense["entry"].endswith("</div>"):
                                prev_sense["entry"] = prev_sense["entry"][:-6]
                            prev_sense["entry_str"] += "".join(line_elem.itertext()) + (line_elem.tail or "")
                            line_str = etree.tostring(line_elem, encoding="Unicode")
                            # Strip outer tag, convert inner tags to lowercase
                            line_str = re.sub(r'</?xml_line>', '', line_str)
                            line_str = re.sub(r'</?[A-Z]>', lambda m : m.group(0).lower(), line_str)
                            prev_sense["entry"] += line_str + "</div>"
                        else: 
                            if prev_entry["entry"].endswith("</div>"):
                                prev_entry["entry"] = prev_entry["entry"][:-6]
                            prev_entry["entry_str"] += "".join(line_elem.itertext()) + (line_elem.tail or "")
                            line_str = etree.tostring(line_elem, encoding="Unicode")
                            # Strip outer tag, convert inner tags to lowercase
                            line_str = re.sub(r'</?xml_line>', '', line_str)
                            line_str = re.sub(r'</?[A-Z]>', lambda m : m.group(0).lower(), line_str)
                            prev_entry["entry"] += line_str + "</div>"
                        continue

                    # Check for additional sense delimiters
                    if is_sense_delim(line_elem[0]):
                        
                        subtag_idx = 0
                        # Add preceding text to previous entry/sense
                        while ( 
                            subtag_idx < len(line_elem) and 
                            not is_sense_delim(line_elem[subtag_idx]) 
                        ):
                            if prev_sense is not None:
                                if prev_sense["entry"].endswith("</div>"):
                                    prev_sense["entry"] = prev_sense["entry"][:-6]
                                prev_sense["entry_str"] += "".join(line_elem.itertext()) + (line_elem.tail or "")
                                prev_sense["entry"] += etree.tostring(line_elem, encoding="Unicode") + "</div>"
                            else: 
                                if prev_entry["entry"].endswith("</div>"):
                                    prev_entry["entry"] = prev_entry["entry"][:-6]
                                prev_entry["entry_str"] += "".join(line_elem.itertext()) + (line_elem.tail or "")
                                prev_entry["entry"] += etree.tostring(line_elem, encoding="Unicode") + "</div>"

                            subtag_idx += 1
                        # Process remaining senses as normal
                        try:
                            # Get preceding senses
                            prev_senses = []
                            i = len(dict_entries)-1
                            while dict_entries[i]["type"] == "sense":
                                prev_senses.insert(0, dict_entries[i])
                                i -= 1
                            addl_senses = parse_senses(
                                line_elem, subtag_idx, prev_entry, 
                                prev_senses = prev_senses if len(prev_senses) > 0 else None
                            )

                            # Final processing for addl_senses
                            prev_sense = addl_senses[-1]
                            for entry in addl_senses:
                                for k,v in entry.items():
                                    if v == "":
                                        entry[k] = SQL_NULL
                                dict_entries.append(entry)

                        except RemediateError as e:
                            remediate_entries.append({ "lemma": e.lemma, "msg": e.msg, "type": e.type})


                    else: 
                        # No extra senses found; append to previous entry/sense
                        if prev_sense is not None:
                            if prev_sense["entry"].endswith("</div>"):
                                prev_sense["entry"] = prev_sense["entry"][:-6]
                            prev_sense["entry_str"] += "".join(line_elem.itertext()) + (line_elem.tail or "")
                            prev_sense["entry"] += etree.tostring(line_elem, encoding="Unicode") + "</div>"
                        else: 
                            if prev_entry["entry"].endswith("</div>"):
                                prev_entry["entry"] = prev_entry["entry"][:-6]
                            prev_entry["entry_str"] += "".join(line_elem.itertext()) + (line_elem.tail or "")
                            prev_entry["entry"] += etree.tostring(line_elem, encoding="Unicode") + "</div>"
                    continue

            # Ordinary entry line
            if line_elem[0].tag != "B": 
                raise ValueError(f"Line does not start with <B> tag: {line_unicode}")
            else: 
                lemma = line_elem[0].text.strip(" \n,;")
                ipa = ipa_oldenglish(lemma)

            # Scan though entry to extract data
            subtag_idx = 1

            try: 
                # Declare variables for entry fields
                orthography = ""
                etymology = ""
                pos = ""
                gender = ""
                entry = ""
                entry_str = ""
                gloss = ""
                entry_senses = []

                # Handle single-tag lines
                if len(line_elem) == 1:
                    if line_elem[0].tail:
                        gloss = entry_str = entry = line_elem[0].tail
                        raise EntryCompleted
                    
                # Check for additional orthographical information
                if line_elem[0].tail: 
                    orthography += line_elem[0].tail
                while (
                    subtag_idx < len(line_elem) and 
                    line_elem[subtag_idx].tag == "I" and 
                    line_elem[subtag_idx].text in lexdata.ORTH
                ):
                    orthography += line_elem[subtag_idx].text
                    orthography += line_elem[subtag_idx].tail
                    subtag_idx += 1

                # Etymology check 1 - after orthography, before POS
                # If present, will be contained in brackets after orthography or POS
                remaining = ""
                lbracket_idx = orthography.find("[")
                warn_no_head = False
                if subtag_idx < len(line_elem) and lbracket_idx != -1: 
                    # Opening bracket found
                    if orthography.strip().endswith("["):
                        warn_no_head = True
                    rbracket_idx = orthography.find("]")
                    if rbracket_idx == -1:
                        etymology = orthography[lbracket_idx:]
                        orthography = orthography[:lbracket_idx].strip(" ,")
                        # Collect remaining etymology data
                        while subtag_idx < len(line_elem): 
                            # Check for closing bracket in text node
                            subtag_text = line_elem[subtag_idx].text
                            bracket_idx_text = subtag_text.rfind("]")
                            if bracket_idx_text == -1: 
                                etymology += subtag_text
                            else: 
                                # Etym brackets closed within text node => 
                                # Capture remaining text for gloss/entry
                                etymology += subtag_text[:bracket_idx_text+1]
                                if gloss != "":
                                    raise RemediateError(lemma, f"Gloss non-empty in Etym check 1. Contents: {gloss}")
                                gloss = subtag_text[bracket_idx_text+1:]
                                break

                            # Check for closing bracket in tail text
                            subtag_tail = (line_elem[subtag_idx].tail or "")
                            bracket_idx_tail = subtag_tail.rfind("]")
                            if bracket_idx_tail == -1: 
                                etymology += subtag_tail
                            else: 
                                etymology += subtag_tail[:bracket_idx_tail+1]
                                remaining = subtag_tail[bracket_idx_tail+1:].lstrip()
                                break

                            # Increment idx after checking both text & tail
                            subtag_idx += 1

                        subtag_idx += 1
                        # print("Etym 1:", etymology)
                        if warn_no_head:
                            remediate_entries.append({"lemma": lemma, "msg": f"No head in etym 1: {etymology}", "type": "WARN"})
                    else: 
                        # Closing bracket found in orthography text => 
                        # not etymology => do nothing
                        pass

                # Prepend lemma (with punct.) to orthography
                orthography = line_elem[0].text + orthography

                # POS check 1 - after orthography
                if subtag_idx < len(line_elem) and not remaining and line_elem[subtag_idx].tag == "I": 
                    subtag_text = line_elem[subtag_idx].text
                    subtag_words = subtag_text.split()
                    if subtag_words[0] in lexdata.POS: 
                        word_idx = 1
                        while ( 
                            " ".join(subtag_words[:word_idx+1]) in lexdata.POS and 
                            word_idx < len(subtag_words)
                            ):
                            word_idx += 1
                        pos = " ".join(subtag_words[:word_idx])
                    elif subtag_words[0] in lexdata.POS_IMPLIES_V: 
                        pos = "v. " + subtag_words[0]
                    elif subtag_words[0] in lexdata.POS_IMPLIES_N: 
                        pos = "n."
                        gender = subtag_words[0]
                    elif ( len(subtag_words) > 1 and 
                        subtag_words[0] in lexdata.POS_W_GLOSS ):
                        if " ".join(subtag_words[:2]) in lexdata.POS_W_GLOSS:
                            pos = "n. " + subtag_words[0]
                            gender = subtag_words[1]
                        else: 
                            pos = "n. " + subtag_words[0]
                            
                # Parse entry & gloss case 1: gloss included in <I> with POS
                if subtag_idx < len(line_elem) and pos != "":
                    subtag_text = line_elem[subtag_idx].text or ""
                    subtag_text_words = subtag_text.split()
                    # Find longest matching substring
                    if gloss != "":
                        raise RemediateError(lemma, f"Gloss non-empty after POS check 1. Contents: {gloss}")

                    # Check for additional text in POS tag:
                    word_idx = 0
                    while ( " ".join(subtag_text_words[:word_idx+1]) in lexdata.POS_REMOVE and 
                        word_idx <= len(subtag_text_words) ):

                        word_idx += 1
                    gloss_text = " ".join(subtag_text_words[word_idx:])
                    if gloss_text.strip() != "":
                        gloss = gloss_text
                        if entry != "":
                            raise RemediateError(lemma, f"Entry non-empty when parsing gloss after POS check 1. Contents: {entry}")
                        entry = f"<I>{gloss}</I>"
                        entry += line_elem[subtag_idx].tail or ""
                        entry_str = gloss
                        entry_str += line_elem[subtag_idx].tail or ""
                        subtag_idx += 1
                        # Parse all remaining words into entry field
                        while subtag_idx < len(line_elem): 
                            subtag = line_elem[subtag_idx]
                            entry += etree.tostring(subtag, encoding="Unicode")
                            entry_str += "".join(subtag.itertext()) + (subtag.tail or "")
                            subtag_idx += 1
                        raise EntryCompleted
                            
                # Etymology check 2 - after POS
                if etymology == "" and subtag_idx < len(line_elem) and pos != "" and gloss == "": 
                    if entry != "":
                        raise RemediateError(lemma, f"Entry non-empty in Etym check 2. Contents: {entry}")
                    if remaining != "":
                        raise RemediateError(lemma, f"'Remaining' non-empty before Etym check 2. Contents: {remaining}")

                    # lbracket_idx = -1
                    # if line_elem[subtag_idx].tail is not None:
                    #     lbracket_idx = line_elem[subtag_idx].tail.find("[")
                    # if subtag_idx < len(line_elem) and lbracket_idx != -1: 
                    #     elem_tag = line_elem[subtag_idx]
                    #     if ( 
                    #         elem_tag.tail is not None and 
                    #         re.match(r' *\]', elem_tag.tail) is not None
                    #     ): 
                    #         etym_tag = line_elem[subtag_idx]
                    #         etymology += orthography[lbracket_idx:]
                    #         etymology += etym_tag.text
                    #         rbracket_idx = etym_tag.tail.find("]")
                    #         etymology += etym_tag.tail[:rbracket_idx]
                    #         orthography = orthography[:lbracket_idx]
                    #         remaining = etym_tag.tail.lstrip(" ]")
                    #         subtag_idx += 1

                    lbracket_idx = line_elem[subtag_idx].tail.find("[") if line_elem[subtag_idx].tail is not None else -1
                    if lbracket_idx != -1:
                        # Opening bracket found
                        rbracket_idx = line_elem[subtag_idx].tail.find("]")
                        if rbracket_idx == -1:
                            etymology = line_elem[subtag_idx].tail[lbracket_idx:]
                            subtag_idx += 1
                            # Collect remaining etymology data
                            while subtag_idx < len(line_elem): 
                                # Check for closing bracket in text node
                                subtag_text = line_elem[subtag_idx].text
                                bracket_idx_text = subtag_text.rfind("]")
                                if bracket_idx_text == -1: 
                                    etymology += subtag_text
                                else: 
                                    # Etym brackets closed within text node => 
                                    # Capture remaining text for gloss/entry
                                    etymology += subtag_text[:bracket_idx_text+1]
                                    if gloss != "":
                                        raise RemediateError(lemma, f"Gloss non-empty in Etym check 2. Contents: {gloss}")
                                    gloss = subtag_text[bracket_idx_text+1:]
                                    break

                                # Check for closing bracket in tail text
                                subtag_tail = (line_elem[subtag_idx].tail or "")
                                bracket_idx_tail = subtag_tail.rfind("]")
                                if bracket_idx_tail == -1: 
                                    etymology += subtag_tail
                                else: 
                                    etymology += subtag_tail[:bracket_idx_tail+1]
                                    remaining = subtag_tail[bracket_idx_tail+1:].lstrip()
                                    break

                                # Increment idx after checking both text & tail
                                subtag_idx += 1

                            subtag_idx += 1
                        else: 
                            # Closing bracket found in orthography text => 
                            # not etymology => do nothing
                            pass
                            # remaining = etymology[bracket_idx+1:].strip()
                            # etymology = etymology[:bracket_idx+1]
                
                if subtag_idx < len(line_elem):
                    # Check for multiple senses in remaining tags
                    has_senses = False
                    before_senses = etree.Element("xmlEntry") # any tags/text falling before first sense delimiter
                    for i in range(subtag_idx, len(line_elem)):
                        e = line_elem[i]
                        if is_sense_delim(e):
                            has_senses = True
                            sense_tag_idx = i
                            break
                        else: 
                            before_senses.append(deepcopy(e))

                    if (
                        len(before_senses) > 0 and has_senses and 
                        # Ignore POS tags
                        not (len(before_senses) == 1 and before_senses[0].text in lexdata.POS_ALL)
                    ):
                        remediate_entries.append({"lemma": lemma, "msg": f"Irregular sense pattern (check sense parsing). Before senses: {etree.tostring(before_senses)}", "type": "WARN"})
                    elif len(before_senses) > 0 and before_senses[0].text in lexdata.POS_ALL:
                        # Remove POS-only tags
                        before_senses.remove(before_senses[0])

                    if has_senses and not before_senses:
                    # Multiple senses, no other content
                        if remaining.strip(" .,") != "":
                            raise RemediateError(lemma, f"'Remaining' non-empty before parse_senses. Contents: {remaining}")
                        entry_senses = parse_senses(line_elem, sense_tag_idx, {"lemma_id": lemma_idx, "lemma": lemma, "page_num": page_num})
                        raise EntryCompleted

                    elif has_senses and before_senses:
                    # Parse entry up to first sense delimiter, then parse senses
                        if entry != "":
                            raise RemediateError(lemma, f"Entry non-empty between E2 & single parsing. Contents: {entry}")

                        if remaining:
                            if re.fullmatch(r'^[ ,.;\])]*$', remaining): 
                                # Eliminate punctuation-only tails
                                remaining = ""
                            entry += remaining
                            remaining = ""
                        
                        if subtag_idx < len(line_elem):
                            subtag_text = line_elem[subtag_idx].text or ""
                            subtag_text_words = subtag_text.split()
                            # Entry case 1: gloss included in <I> with POS
                            # Find longest matching substring
                            if subtag_text_words and subtag_text_words[0] in lexdata.POS_REMOVE:
                                if gloss != "":
                                    raise RemediateError(lemma, f"Gloss non-empty after Etym check 3. Contents: {gloss}")
                                
                                word_idx = 0
                                while ( 
                                    " ".join(subtag_text_words[:word_idx+1]) in lexdata.POS_REMOVE and 
                                    word_idx <= len(subtag_text_words) 
                                ):
                                    word_idx += 1

                                gloss_text = " ".join(subtag_text_words[word_idx+1:])
                                if gloss_text.strip() != "":

                                    gloss = gloss_text
                                    if entry != "":
                                        entry = entry.strip() + " "
                                    entry = f"<I>{gloss}</I>"
                                    entry += line_elem[subtag_idx].tail or ""
                                    entry_str = gloss
                                    entry_str += line_elem[subtag_idx].tail or ""
                                    subtag_idx += 1

                        # Parse remaining data
                        
                            # Case 2: gloss in isolated tag (and not yet parsed)
                            if gloss == "" and line_elem[subtag_idx].tag == "I":
                                gloss = line_elem[subtag_idx].text
                            while ( 
                                subtag_idx < len(line_elem) and 
                                not is_sense_delim(line_elem[subtag_idx])
                            ): 
                                subtag = line_elem[subtag_idx]
                                entry += etree.tostring(subtag, encoding="Unicode")
                                entry_str += "".join(subtag.itertext()) + (subtag.tail or "")
                                subtag_idx += 1
                            if is_sense_delim(line_elem[subtag_idx]):
                                if entry_str.strip() == "":
                                    remediate_entries.append({"lemma": lemma, "msg": f"Entry not found for `before_senses`={etree.tostring(before_senses)}", "type": "WARN"})
                                entry_senses = parse_senses(line_elem, subtag_idx, {"lemma_id": lemma_idx, "lemma": lemma, "page_num": page_num})
                            else: 
                                raise RemediateError({"lemma": lemma, "msg": f"Sense delimiter not found when parsing entry (all tags consumed). Before senses: {etree.tostring(before_senses)}"})
                            raise EntryCompleted

                        else: 
                            # If no tags remain, raise error (should be senses somewhere)
                            raise RemediateError({"lemma": lemma, "msg": f"Sense delimiter not found when parsing entry (no tags remain). Before senses: {etree.tostring(before_senses)}"})
                    else: 
                        # Parse (single) entry & gloss
                        if entry != "":
                            raise RemediateError(lemma, f"Entry non-empty between E2 & single parsing. Contents: {entry}")

                        if remaining:
                            if re.fullmatch(r'^[ ,.;\])]*$', remaining): 
                                # Eliminate punctuation-only tails
                                remaining = ""
                            entry += remaining
                            remaining = ""
                        
                        if subtag_idx < len(line_elem):
                            subtag_text = line_elem[subtag_idx].text or ""
                            subtag_text_words = subtag_text.split()
                            # Entry case 1: gloss included in <I> with POS
                            # Find longest matching substring
                            if subtag_text_words and subtag_text_words[0] in lexdata.POS_REMOVE:
                                if gloss != "":
                                    raise RemediateError(lemma, f"Gloss non-empty after Etym check 3. Contents: {gloss}")
                                
                                word_idx = 0
                                while ( 
                                    " ".join(subtag_text_words[:word_idx+1]) in lexdata.POS_REMOVE and 
                                    word_idx <= len(subtag_text_words) 
                                ):
                                    word_idx += 1

                                gloss_text = " ".join(subtag_text_words[word_idx+1:])
                                if gloss_text.strip() != "":

                                    gloss = gloss_text
                                    if entry != "":
                                        entry = entry.strip() + " "
                                    entry = f"<I>{gloss}</I>"
                                    entry += line_elem[subtag_idx].tail or ""
                                    entry_str = gloss
                                    entry_str += line_elem[subtag_idx].tail or ""
                                    subtag_idx += 1

                        # Parse remaining data
                        
                            # Case 2: gloss in isolated tag (and not yet parsed)
                            if gloss == "" and line_elem[subtag_idx].tag == "I":
                                gloss = line_elem[subtag_idx].text
                            while subtag_idx < len(line_elem): 
                                subtag = line_elem[subtag_idx]
                                entry += etree.tostring(subtag, encoding="Unicode")
                                entry_str += "".join(subtag.itertext()) + (subtag.tail or "")
                                subtag_idx += 1
                            raise EntryCompleted

                        # Case 3: no remaining child tags; entry is remaining tail text
                        elif subtag_idx >= len(line_elem) and entry == "": 
                            entry = line_elem[-1].tail
                            entry_str = line_elem[-1].tail
                            raise EntryCompleted
                        

            except IndexError as ie: 
                print(f"IndexError in lemma {lemma}: {ie}")
                print(lemma, gloss, orthography, etymology, pos, entry, sep="\n")
                save_csv(dict_entries, "bosworth-toller-error.csv")
                raise ie  # Fail loudly
                # Fail quietly; process other entries
                print(f"IndexError in lemma {lemma}: {ie}")  
                continue  # Don't append entry to output list
            except RemediateError as e: 
                remediate_entries.append({ "lemma": e.lemma, "msg": e.msg, "type": e.type })
            except EntryCompleted:
                # All XML elements parsed; jump to entry creation
                # print("Entry completed:", lemma)
                pass

            # Debug exception handler:
            # Prints values for current lemma & outputs
            # partial dict to 'bosworth-toller-error.csv'
            except Exception as e:
                print(f"Exception in lemma {lemma}: {e}")
                print(lemma, gloss, orthography, etymology, pos, entry, sep="\n")
                save_csv(dict_entries, "bosworth-toller-error.csv")
                raise e  # Fail loudly

            # Final cleanup
            etymology = etymology.strip()
            orthography = orthography.strip(" ,;")
            gloss = gloss.strip(" ,;")
            gender = gender.replace(",", ".")
            # Replace capitalized <I> and <B> tags with lowercase
            entry = re.sub(r'</?[BI]>', lambda m : m.group(0).lower(), entry)
            entry = f'<div class="oldenglish bodytext">{entry.strip()}</div>'
            entry_str = entry_str.strip()

            if (
                not entry_senses or 
                entry_senses and before_senses and entry_str
            ):
                # Single entry sense *or*
                # multiple entry senses *and* main sense
                new_entry = {
                    "lemma_id": str(lemma_idx),
                    "lemma": lemma,
                    "sense_num": "",
                    "page_num": str(page_num),
                    "type": "main",
                    "ipa": ipa,
                    "orthography": orthography,
                    "pos": pos,
                    "gender": gender,
                    "etymology": etymology,
                    "entry": entry,
                    "entry_str": entry_str,  # Plaintext of entry (without XML tags)
                    "gloss": gloss,
                    # Sense-only fields
                    "sense_id": "",
                    "h_number": "",
                    "parent_h_number": "",
                }
                if gloss == "" and entry_senses:
                    # Try to borrow gloss from first sense if null
                    remediate_entries.append({"lemma": lemma, "msg": f"Borrowing gloss from first sense: {entry_senses[0]["gloss"]}", "type": "INFO"})
                    new_entry["gloss"] = entry_senses[0]["gloss"]
                if pos == "prep." and len(entry_senses) > 0:
                    remediate_entries.append({"lemma": lemma, "msg": f"Check prep. gloss: {gloss}", "type": "WARN"})
            else: 
                if before_senses: 
                    remediate_entries.append({"lemma": lemma, "msg": f"Main entry not found for `before_senses`={etree.tostring(before_senses)}.", "type": "WARN"})
                    
                # Multiple entry senses
                # Take main entry from first sense
                first_sense = entry_senses.pop(0)
                new_entry = {
                    "lemma_id": str(lemma_idx),
                    "lemma": lemma,
                    "sense_num": first_sense["sense_num"],
                    "page_num": str(page_num),
                    "type": "main",
                    "ipa": ipa,
                    "orthography": orthography,
                    "pos": pos,
                    "gender": gender,
                    "etymology": etymology,
                    "entry": first_sense["entry"],
                    "entry_str": first_sense["entry_str"],  # Plaintext of entry (without XML tags)
                    "gloss": first_sense["gloss"],
                    # Sense-only fields
                    "sense_id": "",
                    "h_number": "",
                    "parent_h_number": "",
                }
                if gloss != "": 
                    print("Lemma:", lemma, "; orig. gloss:", gloss, "; new gloss:", first_sense["gloss"])
                    print("ENTRY SENSES:", entry_senses)
                    raise ValueError("Gloss was nonnull - replaced with sense")

            # Try to impute POS if missing
            if new_entry["pos"] == "":
                # Check gloss
                if new_entry["gloss"] != "":
                    gloss_0 = new_entry["gloss"].split()[0]
                    if gloss_0 in lexdata.IMPUTE_V_GLOSS:
                        new_entry["pos"] = "v."
                    elif gloss_0 in lexdata.IMPUTE_N_GLOSS:
                        new_entry["pos"] = "n."
                # Check orthography
                if new_entry["pos"] == "" and new_entry["orthography"] != "":
                    orth_elem = line_xml(new_entry["orthography"])
                    for tag in orth_elem:
                        if tag.tag == "I" and tag.text in lexdata.IMPUTE_V_ORTH:
                            new_entry["pos"] = "v."
                            break
                        elif tag.tag == "I" and tag.text in lexdata.IMPUTE_N_ORTH:
                            new_entry["pos"] = "n."
                            break

            new_entries = [ new_entry ] + entry_senses

            # Set prev_entry
            prev_entry = new_entry
            prev_sense = entry_senses[-1] if entry_senses else None

            # Handle empty fields, append to dict
            for entry in new_entries:
                for k,v in entry.items():
                    if v == "":
                        entry[k] = SQL_NULL
                dict_entries.append(entry)
            
            lemma_idx += 1
                
    # Write remediate entries out
    with open(REMEDIATE_PATH, "w") as f: 
        writer = csv.DictWriter(f, fieldnames=["lemma", "type", "msg"], delimiter="\t")
        writer.writeheader()
        writer.writerows(remediate_entries)
        if len(remediate_entries) > 0: 
            print(f"See '{REMEDIATE_PATH}' for [{len(remediate_entries)}] manual remediation notices.")

    return dict_entries

def is_sense_delim(xml_elem): 
    '''
    Boolean helper function, returns True
    if provided XML element matches tag & 
    regexp content requirements of *any* 
    sense delimiter tag
    '''

    return (
            xml_elem.tag == "B" and 
            re.fullmatch(r'[A-EI]\.?|[IVXl][IVXl]?[Il]?[Il]?\.?( ?[a-e]\.?)?|1?[0-9]\.', xml_elem.text) 
        )


def parse_senses(line_elem, subtag_idx, lemma_info, *, parent_h_num = None, prev_senses = None):
    global sense_idx
    global remediate_entries
    '''
    Parse and return a list of senses in the provided xml_line element
    Assumes subtag_idx points to a <B> tag in line_elem that begins
    the first dictionary sense.
    Lemma_info is a dict containing lemma_idx, lemma, and page_num 
    from main entry (may just pass a filled-out entry dict)

    Returns a list of sense objects, matching the schema for other 
    dictionary entries above. 
    '''
    if parent_h_num is None: 
        # Instantiate parent_h_num list 
        # (one element for each indentation lvl)
        parent_h_num = [None, None, None, None]

        # If present, populate from prev_senses
        if prev_senses is not None: 
            # Iterate through prev_senses and collect h_num for each level
            # Overwrite appropriate lvl for each subsequent entry
            for s in prev_senses:
                if re.fullmatch(r'[A-E]\.', s["sense_num"]):
                    parent_h_num[0] = s["h_number"]
                elif re.fullmatch(r'[IVX][IVX]?I?I?\.?', line_elem[subtag_idx].text):
                    parent_h_num[1] = s["h_number"]
                elif re.fullmatch(r'[IVX][IVX]?I?I?( ?[a-e])\.?', line_elem[subtag_idx].text):
                    parent_h_num[2] = s["h_number"]
                elif re.fullmatch(r'1?[0-9]\.', line_elem[subtag_idx].text):
                    parent_h_num[3] = s["h_number"]
        
    entry_senses = []
    if line_elem[subtag_idx].tag != "B": 
        raise ValueError("Init. subtag_idx does not point to <B> tag! (in parse_senses)")
    if not is_sense_delim(line_elem[subtag_idx]):
        print(lemma_info)
        print("TAG CONTENTS:", line_elem[subtag_idx].text)
        raise ValueError("Init. <B> tag does not contain sense_num")

    while subtag_idx < len(line_elem):
        # Parse out the rest of the line
        new_sense = {
            "lemma_id": str(lemma_info["lemma_id"]),
            "lemma": lemma_info["lemma"],
            "sense_num": "",  # Filled in below
            "page_num": str(lemma_info["page_num"]),
            "type": "sense",
            # Unique fields
            "entry": "",
            "entry_str": "",
            "gloss": "",
            # Sense-only fields
            "sense_id": str(sense_idx),
            "h_number": "",
            "parent_h_number": "",
            # Intentionally left blank
            "ipa": "",
            "orthography": "",
            "pos": "",
            "gender": "",
            "etymology": "",
        }
        sense_idx += 1
        sense_lvl = 0
        if re.match(r'^[A-E]\.', line_elem[subtag_idx].text):
            new_sense["sense_num"] = line_elem[subtag_idx].text.strip(".")
            sense_lvl = 0
        elif re.match(r'^[IVXl][IVXl]?[Il]?[Il]?\.?$', line_elem[subtag_idx].text):
            new_sense["sense_num"] = line_elem[subtag_idx].text.strip(".")
            sense_lvl = 1
        elif re.match(r'^[IVXl][IVXl]?[Il]?[Il]?\.?( ?[a-e])?\.?$', line_elem[subtag_idx].text):
            new_sense["sense_num"] = line_elem[subtag_idx].text.strip(".")
            sense_lvl = 2
        elif re.match(r'^1?[0-9]\.$', line_elem[subtag_idx].text):
            new_sense["sense_num"] = line_elem[subtag_idx].text.strip(".")
            sense_lvl = 3
        else: 
            raise RemediateError(lemma_info["lemma"], f"sense-initial <B> tag does not contain sense_num. Text contents: {line_elem[subtag_idx].text}")

        # TODO: populate `h_number` and `parent_h_number` fields
        dec_num = len(entry_senses)
        if prev_senses is not None: 
            dec_num += len(prev_senses)
        new_sense["h_number"] = f"n{str(lemma_info["lemma_id"])}.{dec_num}"
        # Find next nonnull parent ID
        parent_lvl = sense_lvl - 1
        # If parent_lvl < 0, leave parent_h_number blank
        if parent_lvl >= 0: 
            # Require parent for senses of level 3 or higher
            require_parent = parent_lvl > 1
            while parent_h_num[parent_lvl] is None and parent_lvl >= 0: 
                parent_lvl -= 1
            if parent_lvl < 0 and require_parent: 
                remediate_entries.append({"lemma":lemma_info["lemma"], "msg": f"No parent found for sense {new_sense["h_number"]} ({new_sense["sense_num"]})", "type": "WARN" })
            elif parent_lvl >= 0:
                new_sense["parent_h_number"] = parent_h_num[parent_lvl]

        if line_elem[subtag_idx].tail is not None and line_elem[subtag_idx].tail.strip() != "": 
            # If sense num tail is nonnull, add to beginning of entry
            new_sense["entry"] += line_elem[subtag_idx].tail.lstrip()

        subtag_idx += 1
        # If last sense and no sub-tags, finalize sense and return
        if subtag_idx >= len(line_elem): 
            # Final cleanup
            # Replace capitalized <I> and <B> tags with lowercase
            new_sense["entry"] = re.sub(r'</?[BI]>', lambda m : m.group(0).lower(), new_sense["entry"])
            new_sense["entry"] = f'<div class="oldenglish bodytext">{new_sense["entry"].strip()}</div>'
            new_sense["entry_str"] = new_sense["entry_str"].strip()

            entry_senses.append(new_sense)
            
            return entry_senses
        
        # Handle case where no subtags in sense entry
        # (Next tag is delimiter for next sense)
        if is_sense_delim(line_elem[subtag_idx]):
            # New sense begins (no gloss found in sense)
            # Final cleanup
            # Replace capitalized <I> and <B> tags with lowercase
            new_sense["entry"] = re.sub(r'</?[BI]>', lambda m : m.group(0).lower(), new_sense["entry"])
            new_sense["entry"] = f'<div class="oldenglish bodytext">{new_sense["entry"].strip()}</div>'
            new_sense["entry_str"] = new_sense["entry_str"].strip()

            entry_senses.append(new_sense)
            parent_h_num[sense_lvl] = new_sense["h_number"]
            continue

        # If tag is <I>, parse gloss
        if line_elem[subtag_idx].tag == "I":
            # Parse gloss from <I> tag
            new_sense["gloss"] = line_elem[subtag_idx].text

        # Parse gloss, entry
        new_sense["entry"] += "".join(line_elem[subtag_idx].itertext()) + (line_elem[subtag_idx].tail or "")
        new_sense["entry_str"] += (line_elem[subtag_idx].text or "") + (line_elem[subtag_idx].tail or "")
        subtag_idx += 1

        while (
            subtag_idx < len(line_elem) and 
            not is_sense_delim(line_elem[subtag_idx])
        ):
            # Parse rest of sense
            new_sense["entry"] += "".join(line_elem[subtag_idx].itertext()) + (line_elem[subtag_idx].tail or "")
            new_sense["entry_str"] += (line_elem[subtag_idx].text or "") + (line_elem[subtag_idx].tail or "")
            subtag_idx += 1

        # Final cleanup
        # Replace capitalized <I> and <B> tags with lowercase
        new_sense["entry"] = re.sub(r'</?[BI]>', lambda m : m.group(0).lower(), new_sense["entry"])
        new_sense["entry"] = f'<div class="oldenglish bodytext">{new_sense["entry"].strip()}</div>'
        new_sense["entry_str"] = new_sense["entry_str"].strip()

        entry_senses.append(new_sense)
        parent_h_num[sense_lvl] = new_sense["h_number"]

    return entry_senses

def save_csv(data, filename):
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()  # Write header row
        writer.writerows(data)  # Write data rows

if __name__ == "__main__":
    startTime = time()
    print("Parsing bosworth-toller-1989.xml")
    entries = get_entries("bosworth-toller-1989.xml")
    save_csv(entries, "bosworth-toller.csv")
    print("Parsing completed.")
    print("Runtime:", time() - startTime, "s")
