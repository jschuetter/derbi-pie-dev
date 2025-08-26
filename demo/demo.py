'''
demo.py
14 August 2025

This is a brief demo of cltk taken from 'cltk/notebooks/CLTK Demonstration.ipynb'
in the CLTK GitHub repository.

I have made some modifications to focus only on Latin and on 
aspects of the package relevant to our purposes.
'''

from cltk import NLP
from cltk.dependency.tree import DependencyTree
from time import time

# Read document
with open("lat-livy.txt") as text:
	livy_full = text.read()
	# Cut down document length for demo
	livy = livy_full[:len(livy_full) // 12]
	print("Approximate token count:", len(livy.split()))

# Load pipeline for Latin
cltk_nlp = NLP(language="lat")
# Remove 'LatinLexiconProcess' for speed
cltk_nlp.pipeline.processes.pop(-1)
print(cltk_nlp.pipeline.processes)

# Analyze text
start_time = time()
cltk_doc = cltk_nlp.analyze(text=livy)
end_time = time()
print(f"Execution time: {end_time - start_time} seconds")

# Print analysis results
print(type(cltk_doc))
print([x for x in dir(cltk_doc) if not x.startswith("__")])  #Print all accessors
# Print a few useful accessors
print(cltk_doc.tokens[:20])
print(cltk_doc.lemmata[:20])
print(cltk_doc.pos[:20])   #parts-of-speech
print(cltk_doc.sentences_tokens[:2])  #First two sentences

# Examine sentence & single word using Doc.words accessor
sentence = cltk_doc.sentences[6]  # type: List[Word]
sentence_str = cltk_doc.sentences_strings[6]  # type: str
print("Original sentence:", sentence_str)
print()
word_str = "concurrunt"
word = [w for w in cltk_doc.words if w.string == word_str][0]
print(f"Properties of Word '{word_str}'")
print(word)

# Morphology modeling
# print("Word features (MorphosyntacticFeatureBundle):")
# print("type(`Word.features`):", type(word.features))
# print()
# print("`Word.features`:", word.features)
# print("\n")

# Syntax modeling
print("Sentence (same as above):", sentence_str)
syntax_tree = DependencyTree.to_tree(sentence)
syntax_tree.print_tree()


# Debugging missing UD feature 'compound'
bad_words = [w for w in cltk_doc.words if ('compound' in w.features)]
print("Error words:")
print([w.string for w in bad_words])
