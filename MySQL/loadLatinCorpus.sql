DROP TABLE corpus_latin_master;
CREATE TABLE corpus_latin_master (
	corpus_latin_master_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255),
    author VARCHAR(255),
    urn VARCHAR(255)
);
-- Insert entries manually
-- Data from https://catalog.perseus.org/catalog/
INSERT INTO corpus_latin_master (title, author, urn)
VALUES (
	"Aeneid",
    "Vergil",
    "urn:cts:latinLit:phi0690.phi003"
);
SELECT * FROM corpus_latin_master;

DROP TABLE corpus_latin_tokens;
CREATE TABLE corpus_latin_tokens (
	id INT PRIMARY KEY AUTO_INCREMENT,
    corpus_latin_master_id INT NOT NULL,
    book_num VARCHAR(64),
	chapter_num VARCHAR(64),
    line_num VARCHAR(64),
    index_token INT NOT NULL,
    index_sentence INT NOT NULL,
    surf_form VARCHAR(255) NOT NULL,
    pos VARCHAR(128),
    lemma VARCHAR(255),
    stem VARCHAR(255),
    dependency_relation VARCHAR(255),
    governor INT,
    features VARCHAR(255),
    category VARCHAR(255),
    syllables VARCHAR(255),
    phonetic_transcription VARCHAR(255)
);

-- Import data from corpus csvs
-- MUST SET CORPUS ID
SELECT corpus_latin_master_id FROM corpus_latin_master
WHERE title = 'Aeneid'
INTO @corpus_id;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/corpus/vergil/aeneid/vergil.aeneid.part.12.csv'
INTO TABLE corpus_latin_tokens
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(index_token,index_sentence,surf_form,pos,lemma,stem,dependency_relation,governor,features,category,syllables,phonetic_transcription, book_num, chapter_num, line_num)
SET corpus_latin_master_id = @corpus_id;

SELECT * FROM corpus_latin_tokens;