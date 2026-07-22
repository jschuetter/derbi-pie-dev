DROP TABLE IF EXISTS temp_on_matching;
CREATE TABLE temp_on_matching (
	lang VARCHAR(10) DEFAULT 'ON',
    lex_ref_link_id INT NOT NULL,
    reflex VARCHAR(255),
    reflex_normalized VARCHAR(255),
    lemma_id INT NOT NULL,
    lemma VARCHAR(255),
    lemma_normalized VARCHAR(255)
);

-- Load data from CSV files
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/matching/oldnorse/unique_matches.csv'
INTO TABLE temp_on_matching
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/matching/oldnorse/duplicate_matches_remediated.csv'
INTO TABLE temp_on_matching
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES;

-- Update lex_ref_link with matches
SELECT * FROM temp_on_matching;
SELECT * FROM lex_ref_link WHERE lang = 'ON';
SELECT COUNT(*) FROM lex_ref_link WHERE lang = 'ON' AND word_id IS NOT NULL;
START TRANSACTION;
SET SQL_SAFE_UPDATES = 0;
UPDATE lex_ref_link l
INNER JOIN temp_on_matching t
ON t.lex_ref_link_id = l.lex_ref_link_id
SET word_id = t.lemma_id
WHERE l.lang = 'ON';
SET SQL_SAFE_UPDATES = 1;
-- ROLLBACK;
-- COMMIT;