import sqlite3

conn=sqlite3.connect("banco.db")
cursor=conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS compras(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        data_compra TEXT,
        valor REAL,
        status TEXT,
        data_pagamento TEXT
)
""")
conn.commit()
conn.close()
print ("Tabela compras criada com sucesso!")