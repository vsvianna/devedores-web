import sqlite3

conn = sqlite3.connect("banco.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    telefone TEXT
)
""")

conn.commit()
conn.close()

print("Banco criado com sucesso!")