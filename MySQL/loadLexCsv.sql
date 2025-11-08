CREATE DATABASE derbi_pie_sql;
USE derbi_pie_sql;
DROP TABLE lewis_short;
CREATE TABLE lewis_short (
	entry_id INT NOT NULL PRIMARY KEY,
    lemma_id INT NOT NULL,
    lemma TEXT NOT NULL,
    parent_id INT, 
    child_ids TEXT,
    sense_num TEXT, 
    page_num INT NOT NULL,
    type TEXT NOT NULL,
    orthography TEXT,
    pos TEXT,
    etymology TEXT,
    entry MEDIUMTEXT,
    entry_str MEDIUMTEXT
);

TRUNCATE TABLE lewis_short;
# Load data from CSV
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/lewis-short.csv'
INTO TABLE lewis_short
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(entry_id, lemma_id, lemma, parent_id, child_ids, sense_num, page_num, type, orthography, pos, etymology, entry, entry_str);

SELECT * FROM lewis_short;