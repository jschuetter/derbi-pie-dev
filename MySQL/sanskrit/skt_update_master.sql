-- lex_master column updates
ALTER TABLE lex_master ADD COLUMN related INT DEFAULT NULL, ALGORITHM=INPLACE, LOCK=NONE;
-- Alternatively, try:
-- ALTER TABLE lex_master ADD COLUMN related INT DEFAULT NULL, ALGORITHM=INSTANT;
ALTER TABLE lex_master MODIFY COLUMN gender VARCHAR(64), ALGORITHM=INPLACE;

-- Add FOREIGN KEY constraints to avoid dropping links
-- Does not work (`lex_ref_link` uses `utf8mb4_0900_ai_ci`; 
-- `lex_master` uses `utf8mb4_unicode_ci`)

-- ALTER TABLE lex_ref_link ADD CONSTRAINT lex_master_id_fk FOREIGN KEY 
-- lex_ref_link (word_id, lang) REFERENCES lex_master (lemma_id, lang);
