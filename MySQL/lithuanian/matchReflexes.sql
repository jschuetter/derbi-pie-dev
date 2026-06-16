USE derbi_pie_jacob;
DROP TABLE IF EXISTS reflex_matches;
CREATE TABLE reflex_matches (
    lang VARCHAR(20) NOT NULL,
    lex_ref_link_id INT NOT NULL,
    reflex VARCHAR(255) NOT NULL,
    reflex_normalized VARCHAR(200) NOT NULL,
    lemma_id int,
    lemma varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    lemma_normalized varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
);

START TRANSACTION;

INSERT INTO reflex_matches
SELECT 'Lith.', lex_ref_link_id, reflex, reflex_normalized, lemma_id, lemma, lemma_normalized
FROM lex_ref_link 
INNER JOIN lex_master
ON reflex_normalized = lemma_normalized COLLATE utf8mb4_unicode_ci
AND lex_ref_link.lang = lex_master.lang COLLATE utf8mb4_unicode_ci
WHERE lex_ref_link.lang = 'Lith.'
LIMIT 3000;

COMMIT;

-- Export matches as CSV
SELECT *
FROM reflex_matches
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/lith_matches.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\n' ;

-- 1537 match rows returned (*including duplicates*), from 1537 rows in lex_ref_link
-- 1178 distinct lemmas matched
-- SELECT COUNT(DISTINCT lex_ref_link_id) FROM reflex_matches;
SELECT * FROM reflex_matches LIMIT 3000;
-- SELECT COUNT(*) FROM lex_ref_link WHERE lang = 'ON';

-- Query unmatched rows
-- INSERT INTO reflex_matches 
-- (lang, lex_ref_link_id, reflex, reflex_normalized)
-- SELECT 'ON', lex_ref_link_id, reflex, reflex_normalized
SELECT lang, lex_ref_link_id, reflex, reflex_normalized, gloss_eng
FROM lex_ref_link 
WHERE lang = 'Lith.' AND NOT EXISTS (
	SELECT lex_ref_link_id FROM reflex_matches WHERE reflex_matches.lex_ref_link_id = lex_ref_link.lex_ref_link_id
);

-- NOTES: 
-- Some reflexes in lex_ref_link match multiple lemmas/homonyms in lex_master
-- Need to capture duplicates *before* updating rows in MySQL
-- => Run SQL query to match entries, save to separate table
-- for export/processing, separate single matches from duplicates,
-- then write updates to lex_master/lex_senses?