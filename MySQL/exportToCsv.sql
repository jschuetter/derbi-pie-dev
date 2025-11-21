SELECT *
FROM lex_ref_link
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/lex_ref_link_2025-11-21_manual.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\n' ;

-- Query to file
SELECT lm.lemma_id, MAX(ms.lemma_orig), lm.entry_str, GROUP_CONCAT(ls.entry_str SEPARATOR '; ')
FROM lex_master lm
JOIN master_stg ms ON ms.lemma_id = lm.lemma_id
LEFT JOIN lex_senses ls ON ls.lemma_id = lm.lemma_id
GROUP BY lm.lemma_id;
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/lex_all_entries.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\n' ;