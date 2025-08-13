[What is a tokenizer (LLMs)? Hugging Face](https://huggingface.co/learn/llm-course/en/chapter2/4)

## Python Packages
- [CLTK](http://cltk.org/)
	- Seems to be most feature-rich, industry standard
	- **Explicitly designed for classical languages** (esp. Latin & Greek)
	- Likely will use some features from here, if nothing else
	- Dr. Byrd reports bugs?
	- Updated every few months; **latest July 12**
- [spaCy](https://spacy.io/usage/models)
	- Well-regarded NLP package
	- No Latin pipeline yet - would have to train
		- [Pipeline training documentation](https://spacy.io/usage/training)
		- Could use [LatinCy](https://huggingface.co/latincy)?
			- Last updated 5-6 months ago
	- **Last updated 3 months ago**
- [Polyglot](https://pypi.org/project/polyglot/)
	- No explicitly-stated support for Latin tokenization?
	- Reportedly good for projects lacking spaCy support [^1]
	- Last updated 5 years ago
- [Mythologos/Sciens](https://github.com/Mythologos/Sciens)
	- Senior capstone project
	- Last updated 6 years ago
- [PyWORDS](https://github.com/sjgallagher2/PyWORDS)
	- Fork of WORDS project
	- Doesn't look like it would suit our purposes
	- Last commit 2 years ago
### Other links
- [latin-BERT](https://github.com/dbamman/latin-bert)
- [Python Natural Language packages with Latin compatibility(?)](https://pypi.org/search/?c=Natural+Language+%3A%3A+Latin)
- [List of parsing packages in Python](https://tomassetti.me/parsing-in-python/)
- [CLTK Latin tokenizer training set](https://github.com/cltk/latin_training_set_sentence_cltk)
- 

## Google AI Responses: 
Several valuable tools exist beyond the Classical Language Toolkit (CLTK) for analyzing and working with Classical Latin texts.

1. Morphological analysis and lemmatization

- **Collatinus:** A free and open-source tool (with desktop and web versions) that provides lemmatization and morphological analysis for Latin texts.
- ~~**LemLat Latin Wordform Lemmatizer:** Developed by the Istituto di Linguistica Computazionale, this tool assists with Latin wordform lemmatization.~~
- ~~**Perseus Digital Library's Word Study Tool:** Offers a morphological analysis feature that helps new students understand word forms and find definitions for Latin, as well as Ancient Greek, Arabic, and Old Norse.~~
- ~~**isidore.co Latin Inflector:** An online tool that analyzes Latin sentences to show each word's part of speech, tense, gender, mood, etc.~~ 

2. Text analysis and research

- **Perseus Digital Library:** A broad collection of resources for linguistic research in various ancient languages, including Latin. It includes searchable versions of dictionaries like Lewis and Short's Latin dictionary.
- **Packard Humanities Institute (PHI) Database:** A database for Latin texts that allows for word and phrase searches.
- **Library of Latin Texts (LLT-A):** A leading database for Latin texts, encompassing a vast collection of Latin words and works.
- **The Latin Library:** Offers digital versions of most major Classical Latin authors.
- **Tesserae:** This project provides a web interface to explore intertextual parallels and compare language in various Latin texts.
- **Lexos:** A web-based tool designed for analyzing, transforming, and visualizing texts, particularly suitable for small to medium-sized collections, including ancient languages. 

1. ~~Latin dictionaries and lexicons~~

- ~~**Numen - The Latin Lexicon:** An online Latin dictionary and grammar tool based on Lewis and Short and An Elementary Latin Dictionary.~~
- ~~**Oxford Latin Dictionary:** Considered the standard English lexicon of Classical Latin.~~
- ~~**Lewis and Short's Latin Dictionary:** A classic Latin-English dictionary available online through the Perseus Project.~~ 

1. ~~Other tools and platforms~~

- ~~**Anki:** A popular flashcard app for creating custom flashcards or downloading pre-made decks for Latin vocabulary and grammar.~~
- ~~**Legentibus:** An app that provides a library of Latin titles for reading practice.~~
- ~~**Vice Verba:** Focuses on honing specific skills like parsing verbs.~~
- ~~**Grammaticus Maximus:** Assists in improving grammatical knowledge.~~ 

**Note:** While CLTK is considered the industry standard for Latin NLP with Python, these alternatives offer various functionalities for different needs and skill levels. For advanced NLP tasks with Latin, exploring Python libraries like SpaCy and NLTK may be beneficial, although they are not specifically designed for ancient languages.

---
While the Classical Language Toolkit (CLTK) is specifically designed for classical languages like Latin, alternatives exist for tokenizing classical Latin in Python, though they may require more manual adaptation to handle Latin-specific linguistic features.

General-Purpose NLP Libraries with Customization:

- **NLTK (Natural Language Toolkit):**
    
    - NLTK offers a wide range of functionalities for NLP, including tokenization.
    - You can use `nltk.word_tokenize` for basic word tokenization.
    - For Latin-specific issues like enclitics (-que, -ne) or postpositive -cum, you would need to implement custom rules or regular expressions to handle these cases during or after the initial tokenization.
    
- **spaCy:**
    
    - spaCy is known for its speed and efficiency in NLP tasks.
    - While spaCy doesn't have a pre-built Latin model with specialized tokenization rules like CLTK, you can create a custom tokenizer by defining your own tokenization rules or by extending an existing language model.
    - This would involve defining patterns for splitting words and handling specific Latin features.
    

Considerations for Latin Tokenization:

When using general-purpose NLP libraries for classical Latin, pay close attention to:

- **Enclitics:**
    
    Latin enclitics like "-que," "-ne," and "-ve" are attached to the preceding word and require special handling to be treated as separate tokens.
    
- **Postpositive -cum:**
    
    The particle "-cum" can be postpositive when used with personal pronouns (e.g., "mecum," "nobiscum"), which might necessitate specific rules for correct tokenization.
    
- **Contractions and Elisions:**
    
    Latin can have contractions and elisions, which may need to be addressed to ensure accurate tokenization for subsequent analysis.
    

In summary: While CLTK provides out-of-the-box solutions for Latin tokenization, NLTK or spaCy can be used as alternatives, provided you implement custom rules to address the unique linguistic features of classical Latin for accurate tokenization.

---

Several alternatives to the Classical Language Toolkit (CLTK) exist for tokenizing Classical Latin in Python, each with varying levels of specialization and complexity:

- **Natural Language Toolkit (NLTK):**
    
    NLTK is a foundational library for NLP in Python and offers general-purpose tokenization functionalities. While it does not inherently account for Latin-specific nuances like enclitics (e.g., "-que", "-ne"), it can be a starting point for basic word and sentence tokenization, especially if custom rules or pre-processing are applied to handle Latin-specific challenges.
    
- **spaCy:**
    
    spaCy is a more modern and performant NLP library designed for production use. It offers advanced tokenization capabilities and can be extended with custom rules or models to handle the intricacies of Latin, although pre-trained models specifically for Classical Latin tokenization may not be as readily available as for modern languages.
    
- **Latin BERT:**
    
    For advanced applications requiring contextual understanding, pre-trained language models like Latin BERT offer a powerful alternative. While primarily designed for tasks like part-of-speech tagging and contextual embeddings, the underlying tokenization used by such models can be leveraged for highly accurate and context-aware word segmentation.
    
- **Custom Implementations based on Whitaker's WORDS:**
    
    Resources like William Whitaker's WORDS program provide extensive morphological data for Latin. Developers can leverage this data to build custom Python scripts or libraries for tokenization and inflection analysis, offering a high degree of control and accuracy for specialized Latin processing tasks.
    
- **Pattern:**
    
    Pattern is another Python library for web mining and NLP, including functionalities like tokenization. It can be used for general text processing and might offer a more lightweight alternative for basic Latin tokenization compared to larger frameworks.
    

The choice of alternative depends on the specific requirements of the project, including the desired level of accuracy, the need for handling Latin-specific linguistic features, and the overall complexity of the NLP pipeline.

[^1]: https://sunscrapers.com/blog/9-best-python-natural-language-processing-nlp/#polyglot
