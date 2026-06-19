import psycopg2

def conectar():
    return psycopg2.connect(
        "postgresql://neondb_owner:npg_nUOiQqS9dpV7@ep-blue-mud-acorati7-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    )