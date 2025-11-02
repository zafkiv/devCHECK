import asyncio
import aiosqlite

async def migrate():
    """Миграция базы данных"""
    db = await aiosqlite.connect('farcaster_monitor.db')
    
    # Проверяем существует ли колонка last_updated
    async with db.execute("PRAGMA table_info(bot_settings)") as cursor:
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'last_updated' not in column_names:
            print("Adding last_updated column...")
            await db.execute("""
                ALTER TABLE bot_settings 
                ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            await db.commit()
            print("✅ Migration completed!")
        else:
            print("✅ Database is up to date")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(migrate())