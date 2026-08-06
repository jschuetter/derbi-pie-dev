SET @lang_code = 'OIr.';

-- Import validated matches from CSV
DROP TABLE IF EXISTS temp_matching;
CREATE TABLE temp_matching (
	lex_ref_link_id INT NOT NULL PRIMARY KEY,
    reflex VARCHAR(255),
    gloss_eng TEXT,
    lemma_id INT NOT NULL,
    lemma VARCHAR(255),
    gloss TEXT,
    entry_str MEDIUMTEXT
);
TRUNCATE TABLE temp_matching;
-- Repeat import for all approved match files (unique + multiple)
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/matching/oldirish/oir_multiple_approved.csv'
INTO TABLE temp_matching
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lex_ref_link_id,reflex,gloss_eng,lemma_id,lemma,gloss,entry_str);

-- Update lex_ref_link with approved matches
SELECT COUNT(*) FROM temp_matching;
START TRANSACTION;
SET SQL_SAFE_UPDATES=0;
UPDATE lex_ref_link r 
INNER JOIN temp_matching t
ON r.lang = @lang_code
AND r.lex_ref_link_id = t.lex_ref_link_id
SET r.word_id = t.lemma_id
WHERE r.lang = @lang_code;
SET SQL_SAFE_UPDATES=1;
SELECT * FROM lex_ref_link WHERE lang = @lang_code;
COMMIT;