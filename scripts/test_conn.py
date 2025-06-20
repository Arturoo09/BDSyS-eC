import os
import psycopg2

try:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "ecommerce_gold"),
        user=os.getenv("POSTGRES_USER", "arturo"),
        password=os.getenv("POSTGRES_PASSWORD", "arturo")
    )
    print("¡CONEXIÓN EXITOSA!")
    conn.close()
except Exception as e:
    print(f"FALLO LA CONEXIÓN: {e}")