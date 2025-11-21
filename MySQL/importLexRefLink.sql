USE derbi_pie_sql;
DROP TABLE lex_ref_link;
CREATE TABLE lex_ref_link (
  orig_lang_abbrev VARCHAR(255) DEFAULT NULL,
  lang VARCHAR(20) DEFAULT NULL,
  lex_ref_link_id INT NOT NULL,
  ref_id VARCHAR(255) DEFAULT NULL,
  rt_ref_link_id INT DEFAULT NULL,
  ref_rt_index INT DEFAULT NULL,
  word_id INT DEFAULT NULL,
  ref_wd_index INT DEFAULT NULL,
  reflex VARCHAR(255) DEFAULT NULL,
  category VARCHAR(255) DEFAULT NULL,
  gloss_orig TEXT,
  gloss_eng TEXT,
  page_loc VARCHAR(20) DEFAULT NULL,
  questionable TINYINT DEFAULT NULL,
  notes TEXT,
  expanded_notes TEXT,
  original_TEXT TEXT,
  created_by VARCHAR(255) DEFAULT NULL,
  last_updated datetime DEFAULT NULL,
  last_updated_by VARCHAR(255) DEFAULT NULL,
  derivation VARCHAR(255) DEFAULT NULL,
  rt_ref_link_id_old INT DEFAULT NULL,
  rt_index INT DEFAULT NULL,
  rt_master_id INT DEFAULT NULL,
  -- PRIMARY KEY (`lex_ref_link_id`),
  KEY `lex_ref_link_ref_id_index` (`ref_id`),
  KEY `lex_ref_link_rt_ref_link_id_index` (`rt_ref_link_id`),
  KEY `lex_ref_link_word_id_index` (`word_id`),
  KEY `lex_ref_link_rt_index_foreign` (`ref_rt_index`)
  -- CONSTRAINT `lex_ref_link_rt_ref_link_id_foreign` FOREIGN KEY (`rt_ref_link_id`) REFERENCES `rt_ref_link` (`rt_ref_link_id`),
--   CONSTRAINT `lex_ref_link_word_id_foreign` FOREIGN KEY (`word_id`) REFERENCES `lex_master` (`lemma_id`)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

# Load data from CSV
TRUNCATE TABLE lex_ref_link;
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/lex_ref_link.csv'
INTO TABLE lex_ref_link
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(@rt_ref_link_id,@rt_ref_link_id_old,orig_lang_abbrev,lex_ref_link_id,ref_id,@ref_rt_index,@word_id,@ref_wd_index,reflex,category,gloss_orig,gloss_eng,@questionable,notes,expanded_notes,original_TEXT,created_by,last_updated_by,@last_updated,@rt_master_id,derivation,@rt_index)
SET questionable = NULLIF(@questionable, '')
AND rt_ref_link_id = NULLIF(@rt_ref_link_id, '')
AND rt_ref_link_id_old = NULLIF(@rt_ref_link_id_old, '')
AND ref_rt_index = NULLIF(@ref_rt_index, '')
AND word_id = NULLIF(@word_id, '')
AND ref_wd_index = NULLIF(@ref_wd_index, '')
AND rt_index = NULLIF(@rt_index, '')
AND rt_master_id = NULLIF(@rt_master_id, '')
AND last_updated = STR_TO_DATE(@last_updated, '%m_%d_%Y_%H%i');

SELECT * FROM lex_ref_link;
SELECT * FROM lex_ref_link WHERE orig_lang_abbrev = 'lat.';

-- Match entries to lexicon
CREATE TABLE lex_ref_link_matches (
	id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    lex_ref_link_id INT,
    lex_ref_link_reflex VARCHAR(255),
    lex_master_id INT,
    lex_master_lemma VARCHAR(255)
);
-- Update this based on format of match file!
-- LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/reflex matching/null_reflexes_with_gloss_matched_2025-11-08.csv'
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/reflex matching/matching_lemmas_2025-11-21.csv'
INTO TABLE lex_ref_link_matches
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
-- (lex_ref_link_id, @match_str, @gloss, @blank, @comments, lex_master_lemma);
(lex_ref_link_reflex, @gloss, @blank, lex_master_lemma, @def, @def);

SELECT * FROM lex_ref_link_matches;
SET SQL_SAFE_UPDATES = 0;
DELETE FROM lex_ref_link_matches WHERE lex_master_lemma = '';
-- Get lex_master_ids
UPDATE lex_ref_link_matches mat 
JOIN master_stg lm
ON lm.lemma_orig = TRIM(mat.lex_master_lemma)
SET mat.lex_master_id = lm.lemma_id
WHERE mat.lex_master_id IS NULL;
-- AND mat.lex_ref_link_id IS NULL  -- Partition update query
-- AND mat.lex_ref_link_reflex < 'g'; 
UPDATE lex_ref_link_matches mat 
LEFT JOIN lex_ref_link lrl 
ON lrl.reflex = mat.lex_ref_link_reflex
SET mat.lex_ref_link_id = lrl.lex_ref_link_id
WHERE mat.lex_ref_link_id IS NULL
AND mat.lex_ref_link_reflex > 'g';

-- Update lex_ref_link
SET SQL_SAFE_UPDATES = 0;
UPDATE lex_ref_link lrl
LEFT JOIN lex_ref_link_matches mat
ON lrl.lex_ref_link_id = mat.lex_ref_link_id
SET lrl.word_id = mat.lex_master_id
WHERE lrl.word_id IS NULL
AND lrl.lex_ref_link_id >= 90000
AND lrl.lex_ref_link_id < 110000;
-- AND mat.lex_ref_link_id IS NULL;

-- Naive matching - from reflex_lemma_link
-- UPDATE lex_ref_link lrl
-- LEFT JOIN reflex_lemma_link mat
-- ON lrl.lex_ref_link_id = mat.lex_ref_link_id
-- SET lrl.word_id = mat.lex_master_id
-- WHERE lrl.word_id IS NULL
-- AND lrl.lex_ref_link_id >= 0000
-- AND lrl.lex_ref_link_id < 10000;

-- Fix '#NAME' entries
SELECT * FROM lex_ref_link WHERE reflex LIKE '#NAME%' AND orig_lang_abbrev LIKE '%lat%';