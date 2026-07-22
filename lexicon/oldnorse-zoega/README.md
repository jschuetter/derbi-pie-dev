# Lexicon - Old Norse 
***A Concise Dictionary of Old Icelandic* (Zoëga)**

This directory contains an XML to CSV parser (`xmlReader.py`) and its corresponding input (`zoega.xml`) and output (`zoega.csv`) for Zoëga's A Concise Dictionary of Old Icelandic. 

The [XML file](https://github.com/clemsciences/old_norse_dictionary_zoega/blob/master/zoegas/dictionary.xml) was sourced from [clemsciences](https://github.com/clemsciences/old_norse_dictionary_zoega/commits?author=clemsciences)' GitHub repository.
The parser script is the original work of [Jacob Schuetter](https://github.com/jschuetter) for the DERBi PIE project.

## Notes
The CLTK IPA transcriber module could not transcribe the lemma 'þrywja', which is an alternate orthography for 'þrumda'.

## MySQL
- `loadLexMaster.sql`: script for loading parsed entries into `lex_master` and `lex_senses`
- `lookupMatch.sql`: a short helper script for looking up matches between `lex_master` and `lex_ref_link`
- `matchReflexes.sql`: exports exact matches found between `lex_ref_link` and `lex_master`
- `loadMatches.sql`: load approved matches from `matches/approved` directory into MySQL