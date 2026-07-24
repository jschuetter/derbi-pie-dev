-- Get count auto-matched
SELECT COUNT(*) AS total_reflexes, COUNT(DISTINCT(lemma_id)) AS matched_reflexes
FROM lex_ref_link r
LEFT JOIN lex_master m
ON reflex = lemma COLLATE utf8mb4_0900_ai_ci
AND r.lang = m.lang COLLATE utf8mb4_0900_ai_ci
WHERE r.lang = 'OE';

-- Select auto-matches into outfile
SELECT r.lex_ref_link_id, r.reflex, r.gloss_eng, m.lemma_id, m.lemma, m.gloss, m.entry_str
FROM lex_ref_link r
JOIN lex_master m
ON reflex = lemma COLLATE utf8mb4_0900_ai_ci
AND r.lang = m.lang COLLATE utf8mb4_0900_ai_ci
WHERE r.lang = 'OE'
ORDER BY lex_ref_link_id
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/oe_literal_matches.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n' ;

-- Import validated matches from CSV
DROP TABLE IF EXISTS temp_oe_matching;
CREATE TABLE temp_oe_matching (
	lex_ref_link_id INT NOT NULL PRIMARY KEY,
    reflex VARCHAR(255),
    gloss_eng TEXT,
    lemma_id INT NOT NULL,
    lemma VARCHAR(255),
    gloss TEXT,
    entry_str MEDIUMTEXT
);
TRUNCATE TABLE temp_oe_matching;
-- Repeat import for all approved match files (unique + multiple)
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/matching/oldenglish/unique_manual_approved.csv'
INTO TABLE temp_oe_matching
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(lex_ref_link_id,reflex,gloss_eng,lemma_id,lemma,gloss,entry_str);

-- Update lex_ref_link with approved matches
SELECT COUNT(*) FROM temp_oe_matching; -- 1888 total matched lemmas
START TRANSACTION;
SET SQL_SAFE_UPDATES=0;
UPDATE lex_ref_link r 
INNER JOIN temp_oe_matching t
ON r.lang = 'OE'
AND r.lex_ref_link_id = t.lex_ref_link_id
SET r.word_id = t.lemma_id
WHERE r.lang = 'OE';
SET SQL_SAFE_UPDATES=1;
SELECT * FROM lex_ref_link WHERE lang = 'OE';
COMMIT;