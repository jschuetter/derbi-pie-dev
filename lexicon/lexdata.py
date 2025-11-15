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

from lxml import etree

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

def xml_to_html(xml_str): 
    """
    Convert XML to HTML using XSLT template
    """
    XSLT_DOC = "./lewis-short-template.xslt"

    try: 
        xml = etree.fromstring(xml_str)
    except etree.XMLSyntaxError as err:
        # Wrap xml string in sense tag if needed
        xml = etree.fromstring("<sense>" + xml_str + "</sense>")
    xslt = etree.parse(XSLT_DOC)

    transform = etree.XSLT(xslt)
    return transform(xml)


def standardize_xml(csv_file_in, csv_file_out): 
    """
    Method for parsing XML to create standardized HTML formatting
    """
    with open(csv_file_in, 'r') as f: 
            reader = csv.DictReader(f)
            data = list(reader)

    for e in data: 
        xml = e["entry"]
        # print(xml)
        e["entry"] = xml_to_html(xml)
        # print(html)
    
    # Write CSV
    print("Writing CSV")
    with open(csv_file_out, 'w') as f: 
        headers = reader.fieldnames
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    # XML_STR = '<sense level="1" n="I" id="n17516.1"> <hi rend="ital">Act.</hi> </sense>'
    XML_STR = '<sense level="5" n="(g)" id="n17511.5"> With <hi rend="ital">ad</hi> and <hi rend="ital">subst.</hi>: <cit><quote lang="la">faciles ad receptum angustiae,</quote> <bibl n="urn:cts:latinLit:phi0914.phi001:32:12:3"><author>Liv.</author> 32, 12, 3</bibl></cit>: <cit><quote lang="la">mens ad pejora,</quote> <bibl n="urn:cts:latinLit:phi1002.phi001:1:2:4"><author>Quint.</author> 1, 2, 4</bibl></cit>: <cit><quote lang="la">credulitas feminarum ad gaudia,</quote> <bibl n="urn:cts:latinLit:phi1351.phi005.perseus-lat1:14:4"><author>Tac.</author> A. 14, 4</bibl></cit>.— <hi rend="ital">Comp.</hi>: <cit><quote lang="la">mediocritas praeceptoris ad intellectum atque imitationem facilior,</quote> <bibl n="urn:cts:latinLit:phi1002.phi001:2:3:1"><author>Quint.</author> 2, 3, 1</bibl></cit>.—</sense>'
    print(xml_to_html(XML_STR))