SELECT lex_ref_link_id, reflex, gloss_orig, gloss_eng, lemma_id, lemma, gloss, entry_str
-- , (SELECT entry_str FROM lex_senses WHERE lex_senses.lemma = reflex COLLATE utf8mb4_unicode_ci LIMIT 1) AS sense_1
FROM lex_ref_link 
INNER JOIN lex_master
ON reflex_normalized = lemma_normalized COLLATE utf8mb4_unicode_ci
AND lex_ref_link.lang = lex_master.lang COLLATE utf8mb4_unicode_ci
WHERE lex_ref_link.lang = 'ON'
AND lemma = 'brýnn';