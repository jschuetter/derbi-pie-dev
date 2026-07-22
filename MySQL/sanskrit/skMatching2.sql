-- Preprocess skt_single_matches for matching
DROP TABLE IF EXISTS temp_match_proc;
CREATE TABLE temp_match_proc AS
SELECT *, REGEXP_REPLACE(REGEXP_REPLACE(parsed_entry_str, '^.*?\\)[ ]*(?:[mfn]{1,3}\.)', ''), ' +', ' ') AS parsed_entry_normalized
FROM skt_single_matches;
SELECT * FROM temp_match_proc WHERE CHAR_LENGTH(parsed_entry_normalized) <= 1
ORDER BY CAST(REPLACE(parsed_id, '*', '') AS UNSIGNED);

-- Insert entries which differ only by transcription
-- Get substring from parsed_entry_str by extracting text after first literal ')'
DROP FUNCTION IF EXISTS match_after_p1;
DROP FUNCTION IF EXISTS match_after_p2;
DROP FUNCTION IF EXISTS match_after_p3;
DROP FUNCTION IF EXISTS match_after_p4;
DROP FUNCTION IF EXISTS match_pfx;
DELIMITER //
-- Return true if entry strings match after first closing parenthesis
CREATE FUNCTION match_after_p1 (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
RETURNS BOOLEAN
DETERMINISTIC
NO SQL
BEGIN
	DECLARE parsed_substr MEDIUMTEXT;
    SET parsed_substr = REGEXP_REPLACE(parsed_entry_str, '^(.*?[\u0900-\u097F\u0980-\u09FF\uA8E0-\uA8FF]\\)){1,4}[ ]*(?:[mfn]{1,3}\.)', '');
    SET parsed_substr = REGEXP_REPLACE(parsed_substr, ' +', ' ');
    RETURN CHAR_LENGTH(parsed_substr) > 1 AND RIGHT(master_entry_str, CHAR_LENGTH(parsed_substr)) = parsed_substr;
END//
-- Return true if entry strings match after second closing parenthesis (i.e. two orthographies)
-- CREATE FUNCTION match_after_p2 (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
-- RETURNS BOOLEAN
-- DETERMINISTIC
-- NO SQL
-- BEGIN
-- 	DECLARE parsed_substr MEDIUMTEXT;
--     SET parsed_substr = REGEXP_REPLACE(parsed_entry_str, '^.*?\\).*?\\)[ ]*(?:[mfn]{1,3}\.)', '');
--     SET parsed_substr = REGEXP_REPLACE(parsed_substr, ' +', ' ');
--     RETURN CHAR_LENGTH(parsed_substr) > 1 AND RIGHT(master_entry_str, CHAR_LENGTH(parsed_substr)) = parsed_substr;
-- END//
-- CREATE FUNCTION match_after_p3 (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
-- RETURNS BOOLEAN
-- DETERMINISTIC
-- NO SQL
-- BEGIN
-- 	DECLARE parsed_substr MEDIUMTEXT;
--     SET parsed_substr = REGEXP_REPLACE(parsed_entry_str, '^.*?\\).*?\\).*?\\)[ ]*(?:[mfn]{1,3}\.)', '');
--     SET parsed_substr = REGEXP_REPLACE(parsed_substr, ' +', ' ');
--     RETURN CHAR_LENGTH(parsed_substr) > 1 AND RIGHT(master_entry_str, CHAR_LENGTH(parsed_substr)) = parsed_substr;
-- END//
-- CREATE FUNCTION match_after_p4 (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
-- RETURNS BOOLEAN
-- DETERMINISTIC
-- NO SQL
-- BEGIN
-- 	DECLARE parsed_substr MEDIUMTEXT;
--     SET parsed_substr = REGEXP_REPLACE(parsed_entry_str, '^.*?\\).*?\\).*?\\).*?\\)[ ]*(?:[mfn]{1,3}\.)', '');
--     SET parsed_substr = REGEXP_REPLACE(parsed_substr, ' +', ' ');
--     RETURN CHAR_LENGTH(parsed_substr) > 1 AND RIGHT(master_entry_str, CHAR_LENGTH(parsed_substr)) = parsed_substr;
-- END//
CREATE FUNCTION match_pfx (parsed_entry_str MEDIUMTEXT, master_entry_str MEDIUMTEXT)
RETURNS BOOLEAN
DETERMINISTIC
NO SQL
BEGIN
	DECLARE parsed_normal MEDIUMTEXT;
    SET parsed_normal = REGEXP_REPLACE(parsed_entry_str, ' +', ' ');
    RETURN CHAR_LENGTH(parsed_normal) > 1 AND LEFT(master_entry_str, CHAR_LENGTH(parsed_normal)) = parsed_normal;
END//
DELIMITER ;

-- SELECT REGEXP_REPLACE('a-kāla—ja (अ-काल—ज) or a-kāla—jāta (अ-काल—जात) or akālôtpanna (अकालो̂त्पन्न),   mfn. born at a wrong time, unseasonable.', '^.*?\\).*?\\)[ ]*', '');

INSERT INTO skt_approved_matches
SELECT * FROM skt_single_matches
WHERE match_after_p1(parsed_entry_str, master_entry_str) = TRUE;
SET SQL_SAFE_UPDATES = 0;
DELETE FROM skt_single_matches
WHERE match_after_p1(parsed_entry_str, master_entry_str) = TRUE;
SET SQL_SAFE_UPDATES = 1;

-- INSERT INTO skt_approved_matches
-- SELECT * FROM skt_single_matches
-- WHERE match_after_p2(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 0;
-- DELETE FROM skt_single_matches
-- WHERE match_after_p2(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 1;

-- INSERT INTO skt_approved_matches
-- SELECT * FROM skt_single_matches
-- WHERE match_after_p3(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 0;
-- DELETE FROM skt_single_matches
-- WHERE match_after_p3(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 1;

-- INSERT INTO skt_approved_matches
-- SELECT * FROM skt_single_matches
-- WHERE match_after_p4(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 0;
-- DELETE FROM skt_single_matches
-- WHERE match_after_p4(parsed_entry_str, master_entry_str) = TRUE;
-- SET SQL_SAFE_UPDATES = 1;

INSERT INTO skt_approved_matches
SELECT * FROM skt_single_matches
WHERE match_pfx(parsed_entry_str, master_entry_str) = TRUE;
SET SQL_SAFE_UPDATES = 0;
DELETE FROM skt_single_matches
WHERE match_pfx(parsed_entry_str, master_entry_str) = TRUE;
SET SQL_SAFE_UPDATES = 1;

-- Update single_matches with paired lemmas
-- INSERT INTO skt_repeat_matches
-- SELECT * FROM skt_single_matches
-- WHERE master_id IN (
-- 	SELECT DISTINCT master_id FROM skt_approved_matches
-- );
-- SET SQL_SAFE_UPDATES = 0;
-- DELETE FROM skt_single_matches
-- WHERE master_id IN (
-- 	SELECT DISTINCT master_id FROM skt_approved_matches
-- );
-- SET SQL_SAFE_UPDATES = 1;

-- Remove duplicates to duplicate table
INSERT INTO skt_duplicate_matches
SELECT * FROM skt_approved_matches
WHERE master_id IN (
	SELECT master_id FROM skt_approved_matches
	GROUP BY master_id HAVING COUNT(*) > 1
);
SET SQL_SAFE_UPDATES = 0;
DELETE FROM skt_approved_matches
WHERE parsed_id IN (
	SELECT DISTINCT parsed_id FROM skt_duplicate_matches
);
SET SQL_SAFE_UPDATES = 1;

SELECT * FROM skt_approved_matches
WHERE master_id IN (
	SELECT master_id FROM skt_approved_matches
	GROUP BY master_id HAVING COUNT(*) > 1
);
SELECT * FROM skt_duplicate_matches;