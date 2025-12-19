CREATE TABLE lex_master (
	lang VARCHAR(32) NOT NULL,
    lemma_id INT NOT NULL PRIMARY KEY,
    lemma VARCHAR(128) NOT NULL,
    gloss MEDIUMTEXT,
    sense_num VARCHAR(64), 
    page_num INT NOT NULL,
    `type` VARCHAR(64) NOT NULL,
    orthography VARCHAR(512),
    ipa VARCHAR(128),
    pos VARCHAR(64),
    gender VARCHAR(16),
    stem VARCHAR(64),
    etymology TEXT,
    entry MEDIUMTEXT,
    entry_str MEDIUMTEXT,
    last_updated DATETIME,
    last_updated_by VARCHAR(16)
);

CREATE TABLE lex_senses(
	lang VARCHAR(32) NOT NULL,
    sense_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    lemma_id INT NOT NULL,
    lemma VARCHAR(128) NOT NULL,
    sense_num VARCHAR(64), 
    page_num INT NOT NULL,
    entry MEDIUMTEXT,
    entry_str MEDIUMTEXT,
    ref_id INT,
    last_updated DATETIME,
    last_updated_by VARCHAR(16)
);