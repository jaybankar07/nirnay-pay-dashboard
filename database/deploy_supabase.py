import os
import psycopg2

SUPABASE_DB_URL = os.getenv(
    "SUPABASE_DATABASE_URL",
    "postgresql://postgres:2124UDSM2077@db.lelvvtepzxvohhxmiram.supabase.co:5432/postgres"
)


def deploy():
    print("Connecting to live Supabase PostgreSQL at db.lelvvtepzxvohhxmiram.supabase.co...")
    conn = psycopg2.connect(SUPABASE_DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # 1. Execute DDL Schema
        schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")
        print(f"Reading schema DDL from {schema_file}...")
        with open(schema_file, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        print("Executing DDL Schema on Supabase PostgreSQL...")
        cursor.execute(schema_sql)
        print("[SUCCESS] DDL Schema deployed successfully.")

        # 2. Execute DML Seed Data
        seed_file = os.path.join(os.path.dirname(__file__), "seed.sql")
        print(f"Reading seed DML from {seed_file}...")
        with open(seed_file, "r", encoding="utf-8") as f:
            seed_sql = f.read()

        print("Executing Seed Data on Supabase PostgreSQL...")
        cursor.execute(seed_sql)
        print("[SUCCESS] Seed Data deployed successfully.")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    deploy()
