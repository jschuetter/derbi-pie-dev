# derbi-pie-dev

The purpose of this repository is to handle the backend data processing for DERBi PIE: a Database of Etymological Roots Beginning in Proto-Indo-European.

## Components
### Lexicon
The Latin language uses the Lewis & Short lexicon, downloaded in XML format from the [Perseus project](https://github.com/PerseusDL/lexica/tree/master/CTS_XML_TEI/perseus/pdllex/lat/ls). To convert this to usable data, `iterReader.py` is used to convert the lexicon to a CSV format for reading into MySQL. The `lexdata.py` file defines several helper methods. This includes two methods for standardizing the XML format into HTML for display on the frontend. The final output is stored in two parts, in `lewis-short-1.csv` and `lewis-short-2.csv`. 

These are both read into the MySQL database using the script `loadLexMaster.sql`. In MySQL, lexicon data are split into two separate tables, `lex_master` and `lex_senses`, where the latter stores additional sense data for the primary entries in `lex_master`. Note that one lemma may have multiple entries in `lex_master` if it may be various parts of speech or have vastly different meanings in different contexts. 

### Corpus & Parser
The second part of this repository parses actual corpus documents, largely taken from the [Tesserae Project](https://github.com/tesserae/tesserae/tree/master/texts/la). The primary parser script is `parser/parse_doc.py`. Provided a file or link as a command-line argument, this script will parse the document in several stages: 
1) Use Classical Language ToolKit (CLTK) to tokenize the text and retrieve grammatical data. (`parse_doc()`)
2) Obtain book, chapter, and line number data from line annotations. (`get_line_annotations()`) **(N.B. this may need to be updated to parse documents not in `.tess` format)**
3) Process the document plaintext to match words to their token ID within the document (for linking in the frontend - `process_doc()`)
	- N.B. document token indices are maintained using a **global variable**, in order to allow parsing documents split into multiple files (see `bulk_parse.py` below). The token index must be reset every time a new document parsing is begun, by calling `reset_doc_token_index()`. This is done automatically in the default pipeline in both `parse_doc.py` and `bulk_parse.py`. 

`bulk_parse.py` is a simple script for parsing a single document in parts. It uses the GitHub API to query documents from a GitHub link, passed in by CLI arguments. Arguments are in the format `<OWNER> <REPO> <PATH>`, or simply `<PATH>`. If `OWNER` and `REPO` are not provided, `Tesserae/Tesserae` is assumed. The `PATH` argument is the path of the file or directory to be parsed, relative to the repository root. 

For example, to parse all the parts of Vergil's Aeneid (found at link https://github.com/tesserae/tesserae/tree/master/texts/la/vergil.aeneid), the arguments would be `tesserae tesserae texts/la/vergil.aeneid`. This will parse all documents in the directory `vergil.aeneid` as parts of a single corpus document. 

> [!WARNING]
> N.B. `bulk_parse.py` assumes all files selected are part of the same document, and tokens will be indexed as such. If multiple files are passed in via the arguments, the token indices will not start at 0 and the `sections.json` file for any documents following the first may include duplicated or incorrect data.

#### Corpus
Parsed files are stored in the `corpus` directory under multiple subdirectories. The `tokens` directory stores the data (in .csv format) from CLTK, organized by author and work. These .csv files match 1-to-1 with the files from which they were derived (i.e. a document that is loaded in four parts will be output in four parts). These .csv files may then be loaded into MySQL by using the `loadCorpusCsv.sql` script. 

> [!IMPORTANT]
> MySQL's default security settings restrict file access to your installation's 'Data' directory, so any files to be imported will need to be moved there, unless you change your settings. More information can be found [here](https://www.mysqltutorial.org/mysql-administration/mysql-data-directory/).

The `texts` directory stores the documents' plaintext in JSON format, where strings are mapped to ID values. If a word (or punctuation mark or the like) does not have a corresponding token in CLTK, it is mapped to `null`. This includes whitespace between characters. These files are divided by book and chapter. The data within each file is also partitioned by line number. This enables easier display on the front end.

## MySQL
> [!NOTE]
> See the [MySQL README](/MySQL/README.md) for details on the MySQL database structure and scripts.

## Dependencies
> [!TIP]
> I set up custom aliases in my Python venv to run the particular Python version (with installed packages) used for this project, since I have multiple installed. To do the same, add these lines at the end of your `.venv/activate` script (or `Activate.ps1`, for Windows):
> ```
> # Add custom aliases
> alias derbipy='/usr/bin/python3.12'
> alias derbipip='derbipy -m pip'
> ```
> If you're not using a [virtual environment](https://docs.python.org/3/library/venv.html), I highly recommend it - it helps keep things isolated when you're working on multiple projects.

- Python 3.12
### Python packages (outside stdlib)
- CLTK: 1.5.0
	- Latest supported Python version is 3.12
	- Install using `pip install cltk==1.5.0`
- lxml: 6.0.1
	- Used for reading lexicon XML files