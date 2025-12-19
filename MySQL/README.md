# derbi-pie MySQL database
All processed data (aside from text JSON files) is served to the frontend using a MySQL database. The overall structure of the database at the time of writing can be found [here](https://drawsql.app/teams/my-schemes/diagrams/copy-of-derbi-pie-db-structure)

## Importing Data
Loading data into the MySQL database is currently done by importing the variety of .csv files generated in this repository. 

> [!INFO]
> Some data can be found in Dr. Byrd's repository, as Excel files. It is important to export these as CSV files *in UTF-8 format*. Otherwise, special characters will not import properly into MySQL. Related import scripts: `importLexRefLink.sql`, `frontend/importMaster.sql`.

### Lexicon
- *lex_master: lemmas mapped to primary definitions*
- *lex_senses: lemmas mapped to subsidiary senses (linked to lex_master)*

Lexicon data is loaded using the `loadLexMaster.sql` script. This first loads all the lexicon data into a temporary table (`master_stg`), then splits it into the production tables `lex_master` (containing the primary definitions for each lemma - *note that there may be several*) and `sense_master` (containing subsidiary senses for each lemma). 

The lexicon data must then be matched to the reflexes in `lex_ref_link`. This is largely a manual process. See `matchReflexDefinition-clean.sql` for some helpful scripts for importing match data. This involves several temporary tables (primarily `reflex_lemma_link`) in order to normalize lemma strings for matching and map them to IDs in both `lex_ref_link` and the `lex_master`. 

> [!INFO]
> Any `SELECT` statements in these scripts are for debugging only and may be skipped in production.

### Corpus
- *corpus_master: corpus document metadata*
- *corpus_latin_tokens: token data for Latin corpus documents*

Corpus data is loaded using the `loadLatinCorpus.sql` file. This is a little more straightforward than the lexicon data, since there need not be any matching. The most complicated part is that some of the data for the documents in `corpus_master` must be loaded manually. This simply entails inserting a row with the document's language, title, and author; along with the source (mostly for archival purposes - `tesserae` for most Latin documents) and URI. 

> [!NOTE]
> The URI represents the subdirectory path where the data for that document may be found in the backend repository. This may depend on how the document is named in the original source repository. Presently, this path is generated at `bulk_parse.py:87-92` or `parse_doc.py:342-350` by parsing the title and author from the Tesserae filename, but this may vary.

The token data is split by language for the sake of balancing managing database size and number of databases. Token data queries must be routed to the correct database by editing the SQL queries in `token.js` in the frontend. Token data for Latin language documents is stored in the table `corpus_latin_tokens`. 

> [!CAUTION]
> When loading token data files, the `corpus_master_id` must be set manually. There is a query to `corpus_master` just above the import statement that will set the appropriate variable.

## Other Scripts
The `MySQL/Archive` directory contains scripts that are (probably) no longer in use, but I was too paranoid to delete.

- `exportToCsv.sql`: does exactly what it says it does - exports a MySQL database to a CSV file. Useful for committing changes (like `lex_ref_link` matches) in the MySQL database to the repository.
- `reflex_lemma_query.sql`: this is a query I used to export some data to help with matching `lex_ref_link` reflexes to lexicon lemmas. 
- `frontend/createUserTable.sql`: creates an empty user table to allow creating/authenticating users and logging in on the frontend.

The `MySQL/db exports` directory contains .CSV exports of some of the tables in my local instance of the database.