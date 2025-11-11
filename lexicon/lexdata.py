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