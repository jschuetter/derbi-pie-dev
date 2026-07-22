# Lexicon - Sanskrit
***A Sanskrit-English Dictionary* (Monier-Williams)**

This directory contains an XML to CSV parser (`xmlreader.py`) and its corresponding input (`monier-williams.xml`) and output (`monier-williams-tempidx.csv`) for the Monier-Williams Sanskrit-English Dictionary.

The [XML file](https://www.sanskrit-lexicon.uni-koeln.de/scans/MW72Scan/2020/web/webtc/download.html) was sourced from [Cologne Digital Sanskrit Dictionaries](https://www.sanskrit-lexicon.uni-koeln.de/).
The parser script is the original work of [Jacob Schuetter](https://github.com/jschuetter) for the DERBi PIE project.

The parser output has had to undergo many rounds of manual remediation and matching to a previous parse. The current source-of-truth output is `skt_reindexed_main.csv` for `lex_master` and `skt_reindexed_senses.csv` for `lex_senses`.