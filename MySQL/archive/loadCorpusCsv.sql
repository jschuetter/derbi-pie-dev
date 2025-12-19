USE derbi_pie_sql;
CREATE TABLE livy_ab_urbe_condita_part1 (
	id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    index_token INT NOT NULL,
    index_sentence INT NOT NULL,
    string TEXT NOT NULL,
    pos TEXT NOT NULL,
    lemma TEXT NOT NULL,
    stem TEXT NOT NULL,
    dependency_relation TEXT NOT NULL,
    governor INT NOT NULL,
    features TEXT,
    category TEXT NOT NULL,
    syllables TEXT NOT NULL,
    phonetic_transcription TEXT NOT NULL
);
# Load data from CSV
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/livy.ab_urbe_condita.part.1.csv'
INTO TABLE livy_ab_urbe_condita_part1
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(index_token,index_sentence,string,pos,lemma,stem,dependency_relation,governor,features,category,syllables,phonetic_transcription);