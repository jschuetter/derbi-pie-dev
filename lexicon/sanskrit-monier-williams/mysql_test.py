import mysql.connector
import os

conn = mysql.connector.connect(
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASS'),
    host=os.getenv('MYSQL_HOST'),
    database=os.getenv('MYSQL_DB')
    )
cursor = conn.cursor()

query = (
    "SELECT MAX(lemma_id) FROM lex_master "
    "WHERE lang = 'Skt.';"
)
cursor.execute(query, ())

print(cursor.fetchone())
# for row in cursor: 
#     print(row)

cursor.close()
conn.close()