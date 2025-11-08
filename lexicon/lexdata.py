"""
lexdata.py
Script for running data through CLTK to get additional lexicon fields
"""
import cltk
from cltk.alphabet.processes import LatinNormalizeProcess
from cltk.lemmatize.processes import LatinLemmatizationProcess
from cltk.phonology import transcription_processes
from cltk.stem.processes import LatinStemmingProcess
from cltk.core.data_types import Word, Doc

import csv
from copy import deepcopy

def add_cltk_data(input_data): 
    """
    Run lemmas through CLTK to get stem & IPA transcription
    input_data is a list of lemmas to process
    N.B. have to batch process Lewis & Short b/c of CLTK's 
    memory constraints
    """
    lemma_corpus = " ".join(set(input_data))
    cltk_nlp = cltk.NLP(language="lat")
    # Replace default pipeline
    cltk_nlp.pipeline.processes = [
        cltk.alphabet.processes.LatinNormalizeProcess,
		cltk.dependency.processes.LatinStanzaProcess,
        transcription_processes.LatinPhonologicalTranscriberProcess,
        cltk.stem.processes.LatinStemmingProcess
    ]
    cltk_out = cltk_nlp.analyze(text=lemma_corpus)
    cltk_dict = {
        word.lemma: {
            "stem": word.stem,
            "ipa": word.phonetic_transcription
        } for word in cltk_out.words
    }

    return cltk_dict

def add_cltk_data_csv(csv_file_in, csv_file_out):
    """
    Same as above, but reads CSV
    """
    with open(csv_file_in, 'r') as f: 
        reader = csv.DictReader(f)
        data = list(reader)

    cltk_doc = Doc(
        language="lat",
        words=[
            Word(
                string=e["lemma"].rstrip("0123456789")
            ) for e in data
        ]
        # raw=" ".join([e["lemma"].rstrip("0123456789") for e in data])
    )
    # print(cltk_doc.raw)
    # cltk_doc = LatinNormalizeProcess().run(input_doc=cltk_doc)
    # cltk_doc = LatinLemmatizationProcess().run(input_doc=cltk_doc)
    cltk_doc = transcription_processes.LatinPhonologicalTranscriberProcess().run(input_doc=cltk_doc)
    cltk_doc = LatinStemmingProcess().run(input_doc=cltk_doc)
    # print(cltk_doc)
    print("CLTK returned")
    for orig, newdata in zip(data, cltk_doc.words): 
        if orig['type'] != 'sense':
            orig['stem'] = newdata.stem if newdata.stem != "" else "\\N"
            orig['ipa'] = newdata.phonetic_transcription if newdata.phonetic_transcription != "" else "\\N"
        else: 
            orig['stem'] = "\\N"
            orig['ipa'] = "\\N"
    
    # Write CSV
    print("Writing CSV")
    with open(csv_file_out, 'w') as f: 
        headers = reader.fieldnames
        headers.append('stem')
        headers.append('ipa')
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

def merge_senses(csv_file_in, csv_file_out, need_merge_file_out=None): 
    """
    Method for merging entries with multiple definitions
    (e.g. 'abactus1' & 'abactus2') into a single parent entry
    with multiple senses
    """
    DIGITS_TUP = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
    DIGITS_STR = '0123456789'
    with open(csv_file_in, 'r') as f: 
        reader = csv.DictReader(f)
        data = list(reader)

    manually_reindex = {}
    
    idx = 0
    lemma_id = 1
    while idx < len(data) - 1: 
        entry = data[idx]
        # print(lemma_id, entry["lemma_id"])
        # assert int(entry["lemma_id"]) == lemma_id

        if entry["lemma"].endswith(DIGITS_TUP):    # If entry has multiple definitions
            # Find other primary definitions
            lem = entry["lemma"].lower().rstrip(DIGITS_STR)
            merge_indices = [idx]
            next_idx = idx + 1
            while data[next_idx]["lemma"].lower().rstrip(DIGITS_STR) == lem:
                # On finding next lemma_id, test lemma
                if not data[next_idx]["lemma_id"] == data[merge_indices[-1]]["lemma_id"]: 
                    # print(data[next_idx]["lemma"], data[merge_indices[-1]]["lemma"])
                    # print(int(data[next_idx]["lemma"][-1]), int(data[merge_indices[-1]]["lemma"][-1]) + 1)
                    # assert int(data[next_idx]["lemma"][-1]) == int(data[merge_indices[-1]]["lemma"][-1]) + 1
                    # Bypassed assertion statement b/c entries 'Nereis1', 'Nereis', 'Nereis2'
                    merge_indices.append(next_idx)
                    # print("Next lemma:", data[next_idx]["lemma"])
                next_idx += 1
            merge_indices.append(next_idx) # Keep idx of next lemma for reference

            # Assert that mergable entries found
            assert len(merge_indices) > 0

            # Create parent entry; update children
            merge_entries = [data[x] for x in merge_indices[:-1]]  # All entries 
            parent_entry = deepcopy(entry)
            parent_entry["lemma"] = lem
            parent_entry["lemma_id"] = lemma_id
            parent_entry["entry"] = "; ".join([
                    f"[{i+1}] " + merge_entries[i]["entry"] if merge_entries[i]["entry"] != "\\N" else f"[{i+1}] " + merge_entries[i]["entry_str"]
                    for i in range(len(merge_entries))
                ])
            parent_entry["entry_str"] = "; ".join([
                    f"[{i+1}] " + merge_entries[i]["entry_str"] for i in range(len(merge_entries))
                ])
            # Update children
            def_num = 1
            # Iterate over all entries and senses in range covered by lemmas
            # print("Merge indices:", merge_indices)
            while def_num < len(merge_indices):
                # print(merge_indices[def_num - 1], ":", merge_indices[def_num])
                for m_ent in data[merge_indices[def_num - 1] : merge_indices[def_num]]: 
                    
                    # print(m_ent["lemma"], lem, def_num)
                    # assert m_ent["lemma"].lower() == lem + str(def_num)
                    if m_ent["lemma"].lower() == lem + str(def_num):
                        m_ent["lemma_id"] = lemma_id
                        if m_ent["sense_num"] != "\\N":
                            m_ent["sense_num"] = f"[{def_num}]." + m_ent["sense_num"]
                        else: 
                            m_ent["sense_num"] = f"[{def_num}]"
                    else: 
                        # If lemma is out of order, mark for manual reindexing
                        print("Needs reindexing", m_ent["lemma"])
                        manually_reindex[m_ent["lemma"]] = lemma_id
                        m_ent["lemma_id"] = "REINDEX"
                        def_number = m_ent["lemma"][-1]
                        # int(def_number)     # Cast to int to check it is a digit
                        # Bypassed assertion statement b/c entries 'Nereis1', 'Nereis', 'Nereis2'
                        if m_ent["sense_num"] != "\\N":
                            m_ent["sense_num"] = f"[{def_number}]." + m_ent["sense_num"]
                        else: 
                            m_ent["sense_num"] = f"[{def_number}]"

                    m_ent["lemma"] = lem
                    m_ent["type"] = "sense"

                def_num += 1

            # Replace original entry with new parent entry
            data.insert(idx, parent_entry)
            # Update idx to next unique lemma
            idx = merge_indices[-1]
            # lemma_id += 1
        else: 
            entry["lemma_id"] = lemma_id
            if data[idx+1]["lemma"].lower() != entry["lemma"].lower().rstrip(DIGITS_STR):
                lemma_id += 1   # Increment index by 1 if no multiple definitions or senses
            idx += 1    
        
        # Increment lemma_id & idx
        # lemma_id += 1

    # Write CSV
    print("Writing CSV")
    with open(csv_file_out, 'w') as f: 
        headers = reader.fieldnames
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    # Output reindexing info
    if need_merge_file_out is not None: 
        with open(need_merge_file_out, 'w') as f: 
            f.write("ENTRIES NEED REINDEXING: ([lemma, prev. idx])\n")
            f.write("\n".join([f"{k} : {v}" for k,v in manually_reindex.items()]))
    else: 
        print("ENTRIES NEED REINDEXING: ([lemma, prev. idx])")
        print("\n".join([f"{k} : {v}" for k,v in manually_reindex.items()]))

if __name__ == "__main__": 
    merge_senses('lewis-short.csv', 'lewis-short-merged.csv')