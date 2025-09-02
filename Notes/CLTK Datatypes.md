https://docs.cltk.org/en/latest/pipelines.html
Refers to [CLTK Demonstration](https://github.com/cltk/cltk/blob/master/notebooks/CLTK%20Demonstration.ipynb) (Jupyter notebook) for further information

# Datatypes
- Word: all processed info for each word
	- Processes add data to words
- Sentence: contain sentence_embeddings (weighted average of word embeddings of sentence)
- Doc: contains original input string (`Doc.raw`) and list of Words (`Doc.words`) - viz. input & output of each Process, NLP()
- Process: takes & returns Doc after processing information & annotating Words in `Doc.words`
- Pipeline: list of Process objects
	- Predefined pipelines available, or can create custom pipelines

## Words
- ***index_char_start***
- ***index_char_stop***
- index_token: index in overall list of tokens
- index_sentence: index of sentence containing token
- string: word text
- pos: part-of-speech
- lemma: dictionary entry
- stem
- *scansion*
- xpos: "treebank-specific POS tag (from Stanza or SpaCy)"
- upos: "universal POS tag (from Stanza or SpaCy)"
- dependency_relation: "(from Stanza or SpaCy)"
- governor: token index of token which governs case? Set to -1 if not governed? (related verb, object, or antecedent?)
	- [reference](https://en.wikipedia.org/wiki/Government_(linguistics))
- features
	- Nouns
		- Case
		- Gender
		- **InflClass**
		- Number
	- Verbs
		- Aspect
		- (Case) - ptc only
		- (Gender) - ptc only
		- **InflClass**
		- (Mood) - finite only
		- Number
		- (Person) - finite only
		- VerbForm
		- Voice
	- Adjectives
		- Case
		- Gender
		- **InflClass**
		- (Numeral) - cardinal/ordinal numbers only
		- Number
	- Adverbs
		- (AdverbialType)
- category: *"The following are the traditional categorial features [+/-N, +/-V] of generative linguistics augmented with the +/-F(unctional) feature as developed by Fukui (1986)."*
	- Functional word
		- *"have little lexical meaning or have ambiguous meaning and express     grammatical relationships among other words within a sentence, or specify the attitude or mood of the speaker"*
	- Nominal word
		- *"a category used to group together nouns and adjectives based on shared properties. The motivation for nominal grouping is that in many languages nouns and adjectives share a number of morphological and syntactic properties."*
	- Verbal word
		- *"typically signal events and actions, can constitute a minimal predicate in a clause, and govern the number and types of other constituents which may occur in the clause."*
- stop: included in stoplist; deemed of too little significance to include in NLP
- *named_entity*
- syllables
- phonetic_transcription
- *definition*
#### Example Cases

| Word       | Iam                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | primum                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | omnium                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | satis                                                                                                                                                                                                                                                                                                                                                                                                                                                               | constat                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Troia                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | capta                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | in                                                                                                                                                                                                                                                                                                                                                                 | ceteros                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | iure                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Attributes | - index_char_start=None<br>- index_char_stop=None<br>- index_token=0<br>- index_sentence=0<br>- string='Iam'<br>- pos=adverb<br>- lemma='iam'<br>- stem=None<br>- scansion=None<br>- xpos='O4\|vgr1'<br>- upos='ADV'<br>dependency_relation='advmod:emph',]<br>- governor=4<br>- features=<br>	- AdverbialType: [time]<br>- category=<br>	- F: [neg]<br>	- N: [pos]<br>	- V: [pos]<br>- stop=True<br>- named_entity=None<br>- syllables=None<br>- phonetic_transcription=None<br>- definition=None | index_char_start=None, <br>index_char_stop=None, <br>index_token=1,<br>index_sentence=0, <br>string='primum', <br>pos=adjective, <br>lemma='primus', <br>stem=None, <br>scansion=None, <br>xpos='B1\|grn1\|casA\|gen3', <br>upos='ADJ', <br>dependency_relation='nsubj', <br>governor=4, <br>features={<br>	Case: [nominative], <br>	Gender: [neuter], <br>	InflClass: [ind_eur_o], <br>	Numeral: [ordinal], <br>	Number: [singular]}, <br>category={<br>	F: [neg], <br>	N: [pos], <br>	V: [pos]}, <br>stop=False, <br>named_entity=None, <br>syllables=None, <br>phonetic_transcription=None, <br>definition=None | index_char_start=None, <br>index_char_stop=None, <br>index_token=2, <br>index_sentence=0, <br>string='omnium', <br>pos=determiner, lemma='omnis', <br>stem=None, <br>scansion=None, xpos='C1\|grn1\|casK\|gen3', <br>upos='DET', <br>dependency_relation='nmod', <br>governor=1, <br>features={<br>    Case: [genitive], <br>	Gender: [neuter], <br>	InflClass: [ind_eur_i], <br>	Number: [plural], <br>	PronominalType: [total]}, <br>category={<br>    F: [pos], <br>	N: [pos], <br>	V: [neg]}, <br>stop=False, <br>named_entity=None, <br>syllables=None, <br>phonetic_transcription=None,<br>definition=None | index_char_start=None, <br>index_char_stop=None, <br>index_token=3, <br>index_sentence=0, <br>string='satis', <br>pos=adverb, <br>lemma='satis', <br>stem=None, <br>scansion=None, <br>xpos='O4', <br>upos='ADV', dependency_relation='advmod', <br>governor=4, <br>features={}, <br>category={<br>    F: [neg], <br>	N: [pos], <br>	V: [pos]}, <br>stop=False, <br>named_entity=None, <br>syllables=None, <br>phonetic_transcription=None, <br>definition=None<br> | index_char_start=None, <br>index_char_stop=None, <br>index_token=4, <br>index_sentence=0, <br>string='constat', <br>pos=verb,<br>lemma='consto', <br>stem=None, <br>scansion=None, <br>xpos='J3\|modA\|tem1\|gen6', upos='VERB', <br>dependency_relation='root', <br>governor=-1, <br>features={<br>    Aspect: [imperfective], <br>	InflClass: [lat_a], <br>	Mood: [indicative], <br>	Number: [singular], <br>	Person: [third], <br>	Tense: [present], <br>	VerbForm: [finite], <br>	Voice: [active]}, <br>category={<br>    F: [neg], <br>	N: [neg], <br>	V: [pos]}, <br>stop=False, <br>named_entity=None, <br>syllables=None, <br>phonetic_transcription=None, <br>definition=None | index_char_start=None, index_char_stop=None, index_token=5, index_sentence=0, string='Troia', pos=noun, lemma='troius', stem=None, scansion=None, xpos='A1\|grn1\|casA\|gen2', upos='NOUN', dependency_relation='nsubj', governor=4, features={Case: [nominative], Gender: [feminine], InflClass: [ind_eur_a], Number: [singular]}, category={F: [neg], N: [pos], V: [neg]}, stop=False, named_entity=None, syllables=None, phonetic_transcription=None, definition=None | index_char_start=None, <br>index_char_stop=None, <br>index_token=6,<br>index_sentence=0, <br>string='capta', <br>pos=verb, <br>lemma='capio', <br>stem=None, <br>scansion=None, <br>xpos='L2\|modM\|tem4\|grp1\|casM\|gen3', upos='VERB', <br>dependency_relation='csubj', <br>governor=4, <br>features={<br>    Aspect: [perfective], <br>	Case: [accusative], <br>	Gender: [neuter], <br>	InflClass: [lat_x, nominal], <br>	Number: [singular], <br>	VerbForm: [participle], <br>	Voice: [passive]}, <br>category={<br>    F: [neg], <br>	N: [neg], <br>	V: [pos]}, <br>stop=False, <br>named_entity=None, <br>syllables=None, <br>phonetic_transcription=None, <br>definition=None | index_char_start=None, index_char_stop=None, index_token=7, index_sentence=0, string='in', pos=adposition, lemma='in', stem=None, scansion=None, xpos='S4', upos='ADP', dependency_relation='case', governor=8, features={}, category={F: [pos], N: [neg], V: [neg]}, stop=True, named_entity=None, syllables=None, phonetic_transcription=None, definition=None), | Word(index_char_start=None, index_char_stop=None, index_token=8, index_sentence=0, string='ceteros', pos=adjective, lemma='ceterus', stem=None, scansion=None, xpos='B1\|grn1\|casM\|gen1', upos='ADJ', dependency_relation='obl', governor=9, features={Case: [accusative], Gender: [masculine], InflClass: [ind_eur_o], Number: [plural]}, category={F: [neg], N: [pos], V: [pos]}, stop=False, named_entity=None, syllables=None, phonetic_transcription=None, definition=None) | index_char_start=None, index_char_stop=None, index_token=20, index_sentence=0, string='iure', pos=noun, lemma='ius', stem=None, scansion=None, xpos='C1\|grn1\|casF\|gen1', upos='NOUN', dependency_relation='orphan', governor=19, features={Case: [ablative], Gender: [masculine], InflClass: [ind_eur_i], Number: [singular]}, category={F: [neg], N: [pos], V: [neg]}, stop=False, named_entity=None, syllables=None, phonetic_transcription=None, definition=None |

## Sentences
## Docs
## Processes
- Processes operate on Doc inputs to annotate Word objects ([[CLTK Datatypes]])
	- Could theoretically add more Processes to add more features
	- [ ] **Examples?**
- [Latin pipeline](https://docs.cltk.org/en/latest/_modules/cltk/languages/pipelines.html#LatinPipeline): (see also [[CLTK Datatypes#Processes]])
	- LatinNormalizeProcess
		- Runs [`cltk.alphabet.lat.normalize_lat`](https://docs.cltk.org/en/latest/cltk.alphabet.html#cltk.alphabet.lat.normalize_lat)
		- Takes a string and optionally removes accents, macrons, and ligatures; and replaces j/v with i/u
	- *LatinTokenizationProcess (default - off)*
		- Imports [`cltk.tokenizers.lat.lat.LatinWordTokenizer`](https://docs.cltk.org/en/latest/cltk.tokenizers.lat.html#cltk.tokenizers.lat.lat.LatinWordTokenizer)
		- Takes input sentence, optionally splits compound words & enclitics, outputs list of tokens
	- [LatinStanzaProcess](https://docs.cltk.org/en/latest/_modules/cltk/dependency/processes.html#LatinStanzaProcess)
		- ***Very possibly source of UD errors?***
		- Imports `cltk.dependency.stanza_wrapper.StanzaWrapper`
		- Sends normalized (or raw) text to Stanza for parsing
		- Converts Stanza output to CLTK format
		- Outputs updated Doc with new words & doc from Stanza
		- *Likely what produces most Word feature annotations?*
	- *LatinSpacyProcess (default - off)*
		- Refers to same file as LatinStanzaProcess
		- Seems to have same functionality as LatinStanzaProcess, but uses SpaCy instead of Stanza for parsing?
		- Could be a valid option if Stanza isn't giving us what we need (Stanza is probably more up-to-date?)
	- LatinEmbeddingsProcess
		- [ ] ***Figure out what output of this process looks like - do we need it?***
		- Depends on multiple pkgs from `cltk.embeddings.embeddings`
	- StopsProcess
		- "Note this marks a word a stop if there is a match on either the inflected form (`Word.string`) or the lemma (`Word.lemma`)."
		- viz. marks 'true' if word is not compound or does not have clitic?
	- *LatinNERProcess (default - off)*
		- Named-Entity Recognition
		- May return list of True/False for each token, or True values replaced by entity type token (e.g. LOC)
	- LatinLexiconProcess (*disabled in demo*)
		- "Latin dictionary lookup algorithm" (uses LatinLewisLexicon)
		- What does this output?

# [Packages](https://docs.cltk.org/en/latest/cltk.html#cltk.nlp.NLP)
***What are these?***
## Used in default processes
- [alphabet.lat.normalize_lat](https://docs.cltk.org/en/latest/cltk.alphabet.html#cltk.alphabet.lat.normalize_lat)
	- [Docs](https://docs.cltk.org/en/latest/cltk.alphabet.html#module-cltk.alphabet.lat)
	- Used in [LatinNormalizeProcess](https://docs.cltk.org/en/latest/cltk.alphabet.html#module-cltk.alphabet.processes)
- [lemmatize.lat](https://docs.cltk.org/en/latest/cltk.lemmatize.html#module-cltk.lemmatize.lat)
	- Cf. [LatinLemmatizationProcess](https://docs.cltk.org/en/latest/cltk.lemmatize.html#cltk.lemmatize.processes.LatinLemmatizationProcess)
- [lexicon.lat](https://docs.cltk.org/en/latest/cltk.lexicon.html#module-cltk.lexicon.lat)
	- Cf. [LatinLexiconProcess](https://docs.cltk.org/en/latest/cltk.lexicon.html#cltk.lexicon.processes.LatinLexiconProcess)
- [stops.lat](https://docs.cltk.org/en/latest/cltk.stops.html#module-cltk.stops.lat)
	- Cf. StopsProcess
- [tokenizers.lat](https://docs.cltk.org/en/latest/cltk.tokenizers.lat.html)
	- Cf. LatinTokenizationProcess
## Not used in default processes
- [corpora.lat](https://docs.cltk.org/en/latest/cltk.corpora.lat.html)???
- [morphology.lat](https://docs.cltk.org/en/latest/cltk.morphology.html#module-cltk.morphology.lat)
- [phonology.lat](https://docs.cltk.org/en/latest/cltk.phonology.lat.html)
	- Phonology, syllabifier, transcription submodules
- [prosody.lat](https://docs.cltk.org/en/latest/cltk.prosody.lat.html)
	- Many submodules
- [sentence.lat](https://docs.cltk.org/en/latest/cltk.sentence.html#module-cltk.sentence.lat)
- [stem.lat](https://docs.cltk.org/en/latest/cltk.stem.html#module-cltk.stem.lat)
- [text.lat](https://docs.cltk.org/en/latest/cltk.text.html#module-cltk.text.lat)
