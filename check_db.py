import sqlite3

# Создаём новую БД с правильной структурой
conn = sqlite3.connect('farcaster_monitor.db')
cursor = conn.cursor()

# Таблица monitored_fids
cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitored_fids (
        fid INTEGER PRIMARY KEY,
        username TEXT,
        last_cast_hash TEXT,
        last_checked TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        casts_sent INTEGER DEFAULT 0
    )
""")

# Таблица bot_settings
cursor.execute("""
    CREATE TABLE IF NOT EXISTS bot_settings (
        id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
        admin_user_id INTEGER,
        alert_group_id INTEGER,
        is_active BOOLEAN DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Вставляем дефолтную запись
cursor.execute("""
    INSERT OR REPLACE INTO bot_settings (id, is_active, last_updated)
    VALUES (1, 1, CURRENT_TIMESTAMP)
""")

conn.commit()

# Проверяем структуру
print("\n=== Структура таблицы bot_settings ===")
cursor.execute("PRAGMA table_info(bot_settings)")
for row in cursor.fetchall():
    print(f"{row[1]}: {row[2]}")

print("\n=== Данные в bot_settings ===")
cursor.execute("SELECT * FROM bot_settings")
for row in cursor.fetchall():
    print(row)

conn.close()
print("\n✅ База данных создана правильно!")