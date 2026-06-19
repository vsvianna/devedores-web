
from database import conectar
conn=conectar()
cursor=conn.cursor()

cursor.execute("""
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL
)
""")

cursor.execute("""
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    telefone VARCHAR(50),
    usuario_id INTEGER REFERENCES usuarios(id)
)
""")

cursor.execute("""
CREATE TABLE compras (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    data_compra DATE,
    valor NUMERIC(10,2),
    status VARCHAR(20),
    data_pagamento DATE
)
""")

conn.commit()
conn.close()

print("Banco de dados criado.")