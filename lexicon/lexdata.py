"""
lexdata.py
Script for running data through CLTK to get additional lexicon fields
"""
import cltk
from cltk.phonology import transcription_processes

def add_cltk_data(input_data): 
    '''
    Run lemmas through CLTK to get stem & IPA transcription
    input_data is a list of lemmas to process
    N.B. have to batch process Lewis & Short b/c of CLTK's 
    memory constraints
    '''
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