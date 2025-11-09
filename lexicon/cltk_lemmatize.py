"""
cltk_lemmatize.py
Script for running data through CLTK to get lemmas for matching
"""
import cltk
from cltk.alphabet.processes import LatinNormalizeProcess
from cltk.lemmatize.processes import LatinLemmatizationProcess
from cltk.core.data_types import Word, Doc

import csv

def cltk_lemmatize(csv_file_in, csv_file_out):
    """
    Same as above, but reads CSV
    """
    with open(csv_file_in, 'r') as f: 
        reader = csv.DictReader(f)
        data = list(reader)

    text = " ".join([e["match_str"] for e in data])
    cltk_nlp = cltk.NLP(language="lat")
	# Default: 
		# 'cltk.alphabet.processes.LatinNormalizeProcess'
		# 'cltk.dependency.processes.LatinStanzaProcess'
		# 'cltk.embeddings.processes.LatinEmbeddingsProcess'
		# 'cltk.stops.processes.StopsProcess'
		# 'cltk.lexicon.processes.LatinLexiconProcess'

	# Customize pipeline
	# Pop embeddings process
    remove_processes = [
        cltk.embeddings.processes.LatinEmbeddingsProcess,
        cltk.stops.processes.StopsProcess,
        cltk.lexicon.processes.LatinLexiconProcess
    ]
    cltk_nlp.pipeline.processes = [p for p in cltk_nlp.pipeline.processes if p not in remove_processes]
    print(cltk_nlp.pipeline.processes)
    cltk_doc = cltk_nlp.analyze(text=text)
    # cltk_doc = Doc(
    #     language="lat",
    #     words=[
    #         Word(
    #             string=e["match_str"]
    #         ) for e in data
    #     ]
    #     # raw=" ".join([e["lemma"].rstrip("0123456789") for e in data])
    # )
    # print(cltk_doc.raw)
    # cltk_doc = LatinNormalizeProcess().run(input_doc=cltk_doc)
    # cltk_doc = LatinLemmatizationProcess().run(input_doc=cltk_doc)
    # print(cltk_doc.words)
    print("CLTK returned")
    unmatched = {}
    data_idx = 0
    cltk_idx = 0
    while data_idx < len(data) and cltk_idx < len(cltk_doc.words):
        d = data[data_idx]
        l = cltk_doc.words[cltk_idx]
        print(d["match_str"], l.string)
        # assert orig["match_str"] == newdata.string
        if d["match_str"] == l.string:
            d["lemma"] = l.lemma
            data_idx += 1
            cltk_idx += 1
        else: 
            # Skip broken tokens in CLTK
            unmatched[d["lemma"]] = l.string
            data_idx += 1
            cltk_idx += 2
    print("Unmatched:")
    print("\n".join([f"{k}:{v}" for k, v in unmatched.items()]))

    # Write CSV
    print("Writing CSV")
    with open(csv_file_out, 'w') as f: 
        headers = reader.fieldnames
        headers.append('lemma')
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__": 
    cltk_lemmatize('../MySQL/unmatched_reflexes_master.csv', '../MySQL/unmatched_reflexes_lemmas.csv')