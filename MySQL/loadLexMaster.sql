CREATE DATABASE derbi_pie_sql;
USE derbi_pie_sql;
-- Staging table to load data from CSV, to be split into lex_master and lex_senses
DROP TABLE master_stg;
CREATE TABLE master_stg (
	entry_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    lemma_id INT NOT NULL,
    lemma VARCHAR(128) NOT NULL,
    sense_num VARCHAR(64), 
    page_num INT NOT NULL,
    `type` VARCHAR(64) NOT NULL,
    orthography VARCHAR(512),
    ipa VARCHAR(128),
    pos VARCHAR(64),
    stem VARCHAR(64),
    etymology TEXT,
    entry MEDIUMTEXT,
    entry_str MEDIUMTEXT
);

TRUNCATE TABLE master_stg;
# Load data from CSV
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/lewis-short.csv'
INTO TABLE master_stg
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lemma_id, lemma, sense_num, page_num, `type`, orthography, pos, etymology, entry, entry_str, stem, ipa);

SELECT * FROM master_stg;

DROP TABLE lex_master;
CREATE TABLE lex_master (
	lang VARCHAR(32) NOT NULL,
    lemma_id INT NOT NULL PRIMARY KEY,
    lemma VARCHAR(128) NOT NULL,
    gloss MEDIUMTEXT,
    sense_num VARCHAR(64), 
    page_num INT NOT NULL,
    `type` VARCHAR(64) NOT NULL,
    orthography VARCHAR(512),
    ipa VARCHAR(128),
    pos VARCHAR(64),
    gender VARCHAR(16),
    stem VARCHAR(64),
    etymology TEXT,
    entry MEDIUMTEXT,
    entry_str MEDIUMTEXT,
    last_updated DATETIME,
    last_updated_by VARCHAR(16)
);

-- Insert data from master_stg into lex_master
INSERT INTO lex_master 
(
	lang, 
	lemma_id, 
	lemma, 
	gloss, 
	sense_num, 
	page_num, 
	`type`, 
	orthography, 
    ipa,
	pos, 
	gender, 
	stem, 
	etymology,
    entry, 
    entry_str, 
    last_updated, 
    last_updated_by
)
SELECT 
	'lat.', 
    lemma_id, 
    lemma, 
    entry_str, 
    sense_num, 
    page_num, 
    `type`, 
    orthography, 
    ipa,
    pos, 
    NULL,
    stem,
    etymology,
    entry,
    entry_str,
    CURTIME(),
    'jms'
FROM master_stg
WHERE `type` != 'sense';

-- Update glosses with little/no entry (references to Müll.)
SET SQL_SAFE_UPDATES = 0;
UPDATE lex_master
SET gloss = CONCAT(orthography, ' Müll.'),
entry_str = CONCAT(orthography, ' Müll.')
WHERE gloss='Müll.';
SET SQL_SAFE_UPDATES = 1;

-- Parse gender for noun entries
UPDATE lex_master
SET gender = SUBSTRING(pos, 4),
pos = SUBSTRING(pos, 1, LOCATE('.', pos))
WHERE SUBSTRING(pos, 1, 1) = 'n';

SELECT * FROM lex_master;

-- Make lex_senses table
DROP TABLE lex_senses;
CREATE TABLE lex_senses(
	lang VARCHAR(32) NOT NULL,
    sense_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    lemma_id INT NOT NULL,
    lemma VARCHAR(128) NOT NULL,
    sense_num VARCHAR(64), 
    page_num INT NOT NULL,
    orthography VARCHAR(512),
    ipa VARCHAR(128),
    pos VARCHAR(64),
    gender VARCHAR(16),
    stem VARCHAR(64),
    etymology TEXT,
    entry MEDIUMTEXT,
    entry_str MEDIUMTEXT,
    ref_id INT,
    last_updated DATETIME,
    last_updated_by VARCHAR(16)
);

-- Copy sense data from master_stg
INSERT INTO lex_senses 
(
	lang, 
	lemma_id, 
	lemma, 
	sense_num, 
	page_num, 
	orthography, 
    ipa,
	pos, 
	gender, 
	stem, 
	etymology,
    entry, 
    entry_str,
    last_updated, 
    last_updated_by
)
SELECT 
	'lat.', 
    lemma_id, 
    lemma, 
    sense_num, 
    page_num, 
    orthography, 
    ipa,
    pos, 
    NULL,
    stem,
    etymology,
    entry,
    entry_str,
    CURTIME(),
    'jms'
FROM master_stg
WHERE `type` = 'sense';

-- Parse gender for noun entries
UPDATE lex_senses
SET gender = SUBSTRING(pos, 4),
pos = SUBSTRING(pos, 1, LOCATE('.', pos))
WHERE SUBSTRING(pos, 1, 1) = 'n';

SELECT * FROM lex_senses;