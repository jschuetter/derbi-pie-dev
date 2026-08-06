SET @lang_code = 'OIr.';

-- Get count auto-matched
SELECT COUNT(*) AS total_reflexes, COUNT(DISTINCT(lemma_id)) AS matched_reflexes
FROM lex_ref_link r
LEFT JOIN lex_master m
ON reflex = lemma COLLATE utf8mb4_0900_ai_ci
AND r.lang = m.lang COLLATE utf8mb4_0900_ai_ci
WHERE r.lang = @lang_code;

-- Display results
SELECT r.lex_ref_link_id, r.reflex, r.gloss_eng, m.lemma_id, m.lemma, m.gloss, m.entry_str
FROM lex_ref_link r
JOIN lex_master m
ON reflex = lemma COLLATE utf8mb4_0900_ai_ci
AND r.lang = m.lang COLLATE utf8mb4_0900_ai_ci
WHERE r.lang = @lang_code
ORDER BY lex_ref_link_id;

-- Select auto-matches into outfile
SELECT r.lex_ref_link_id, r.reflex, r.gloss_eng, m.lemma_id, m.lemma, m.gloss, m.entry_str
FROM lex_ref_link r
JOIN lex_master m
ON reflex = lemma COLLATE utf8mb4_0900_ai_ci
AND r.lang = m.lang COLLATE utf8mb4_0900_ai_ci
WHERE r.lang = @lang_code
ORDER BY lex_ref_link_id
INTO OUTFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/exports/literal_matches.csv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' 
ESCAPED BY '\\'
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n' ;