SELECT * FROM lex_ref_link WHERE lang = 'Lith.';
SELECT * FROM lex_master WHERE lang = 'Lith.' ORDER BY lemma;
SELECT COUNT(*) FROM lex_ref_link WHERE lang = 'Lith.';
SELECT COUNT(*) FROM lex_master WHERE lang = 'Lith.';

DROP TABLE IF EXISTS temp_lith_matching;
CREATE TABLE temp_lith_matching (
	lex_ref_link_id INT,
    reflex VARCHAR(128),
    gloss_eng MEDIUMTEXT,
    lemma_id INT,
    lemma VARCHAR(128),
    gloss MEDIUMTEXT
);
CREATE TABLE temp_lith_master
AS SELECT * FROM lex_master WHERE lang = 'Lith.';
CREATE TABLE temp_lith_link
AS SELECT * FROM lex_ref_link WHERE lang = 'Lith.';

TRUNCATE TABLE temp_lith_matching;
-- INSERT INTO temp_lith_matching
SELECT lrl.lex_ref_link_id, lrl.reflex_normalized, lrl.gloss_eng, lm.lemma_id, lm.lemma_normalized, lm.gloss
FROM temp_lith_link lrl
JOIN temp_lith_master lm
ON lrl.reflex_normalized = lm.lemma_normalized COLLATE utf8mb4_0900_ai_ci
ORDER BY lrl.lex_ref_link_id;

SELECT COUNT(DISTINCT lex_ref_link_id) FROM temp_lith_matching;

-- Export duplicates separately
SELECT *
FROM temp_lith_matching
WHERE lex_ref_link_id IN (
	SELECT lex_ref_link_id 
    FROM temp_lith_matching
    GROUP BY lex_ref_link_id
    HAVING COUNT(*) > 1
)
ORDER BY lex_ref_link_id
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/lith_dupl_matches.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n' ;
-- Single matches
SELECT *
FROM temp_lith_matching
WHERE lex_ref_link_id IN (
	SELECT lex_ref_link_id 
    FROM temp_lith_matching
    GROUP BY lex_ref_link_id
    HAVING COUNT(*) = 1
)
ORDER BY lex_ref_link_id
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/lith_uniq_matches.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n' ;