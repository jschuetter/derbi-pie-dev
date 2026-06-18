import mysql.connector
import os

# Init. MySQL connection
conn = mysql.connector.connect(
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASS'),
    host=os.getenv('MYSQL_HOST'),
    database=os.getenv('MYSQL_DB')
    )
db = conn.cursor()

# Next available indices in MySQL
db.execute((
    "SELECT MAX(lemma_id) FROM lex_master "
    "WHERE lang = 'Skt.';"
))
next_lemma_idx = db.fetchone()[0] + 1
db.execute((
    "SELECT MAX(sense_id) FROM lex_senses "
    "WHERE lang = 'Skt.';"
))
next_sense_idx = db.fetchone()[0] + 1
print("Next available indices:", next_lemma_idx, "(lemmas),", next_sense_idx, "(senses)")

# Try to retrieve lemma_id from MySQL

# Maintain lists of (lemma_id, lemma) pairs that
# were found, not found or multiples found in MySQL
# Will be exported to JSON format when execution finishes
# matched_lemmas = []  # dict format: {lemma_id, lemma, entry, orig_lemma, orig_entry}
# unmatched_lemmas =  []  # dict format: {lemma_id, lemma, entry} (new ID generated)
# multiple_match_lemmas = []  # dict format: {lemma_id, lemma, entry, matches (list of entries in same format)}

# print("Lemma/pg:", new_entry["lemma_translit"], "/", new_entry["page_num"])
# if new_entry["type"] != "sense":
#     lemma_query = (
#         "SELECT lemma_id, lemma, entry_str FROM lex_master "
#         "WHERE lemma LIKE %s "
#         "AND page_num = %s"
#     )
#     db.execute(lemma_query, (f"{new_entry["lemma_translit"]} (%)", new_entry["page_num"]))
#     lemma_matches = db.fetchall()
#     print("Matches:", *lemma_matches)
#     if len(lemma_matches) > 1: 
#         # Many matches; need to remediate manually
#         multiple_match_lemmas.append({
#             "lemma_id": new_entry["lemma_id"],
#             "lemma": new_entry["lemma_translit"],
#             "entry_str": new_entry["entry_str"],
#             "matches": [
#                 {
#                     "lemma_id": row[0],
#                     "lemma": row[1],
#                     "entry_str": row[2]
#                 } for row in lemma_matches
#             ]
#         })
#     elif len(lemma_matches) < 1: 
#         # No match found
#         new_entry["lemma_id"] = next_lemma_idx
#         unmatched_lemmas.append({
#             "lemma_id": next_lemma_idx,
#             "lemma": new_entry["lemma_translit"],
#             "entry_str": new_entry["entry_str"]
#         })
#         next_lemma_idx += 1
#     else: 
#         # Exactly one match found
#         assert len(lemma_matches) == 1

#         # TODO: add assertion to check that lemma does actually match

#         new_entry["lemma_id"] = lemma_matches[0][0]
#         matched_lemmas.append({
#             "lemma_id": new_entry["lemma_id"],
#             "lemma": new_entry["lemma_translit"],
#             "entry_str": new_entry["entry_str"],
#             "orig_lemma": lemma_matches[0][1],
#             "orig_entry_str": lemma_matches[0][2],
#         })

db.close()
conn.close()