SELECT * FROM lex_master WHERE lang = 'Skt.' AND gender LIKE 'mf%n.';
START TRANSACTION;
UPDATE lex_master
SET pos = "adj."
WHERE lang = 'Skt.'
AND gender LIKE 'mf%n.';
-- 58536 rows updated
-- ROLLBACK;
COMMIT;