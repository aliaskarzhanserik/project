import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "database.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
SEED_PATH = BASE_DIR / "seed.sql"

def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("🗑️ Старая база данных удалена.")

    try:
        with sqlite3.connect(DB_PATH) as conn:
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            print("🏗️ Схема создана.")
            
            with open(SEED_PATH, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            print("🌱 Данные загружены.")
        print("✅ База данных успешно готова!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()