# services/database.py
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DatabaseService:
    """Сервис для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str = "farcaster_monitor.db"):
        self.db_path = db_path
        self.conn = None
        self._init_database()
        logger.info("✅ Database initialized")
    
    def _init_database(self):
        """Инициализация базы данных и создание таблиц"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Таблица настроек бота
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Таблица отслеживаемых пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitored_users (
                fid INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица кастов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS casts (
                hash TEXT PRIMARY KEY,
                fid INTEGER NOT NULL,
                text TEXT,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fid) REFERENCES monitored_users(fid)
            )
        ''')
        
        self.conn.commit()
    
    # === Методы для настроек бота ===
    
    def set_admin_user(self, user_id: int):
        """Установить администратора бота"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)',
            ('admin_user_id', str(user_id))
        )
        self.conn.commit()
        logger.info(f"✅ Admin user set: {user_id}")
    
    def set_alert_group(self, group_id: int):
        """Установить группу для уведомлений"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)',
            ('alert_group_id', str(group_id))
        )
        self.conn.commit()
        logger.info(f"✅ Alert group set: {group_id}")
    
    def get_bot_settings(self) -> Dict[str, str]:
        """Получить все настройки бота"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT key, value FROM bot_settings')
        
        settings = {}
        for row in cursor.fetchall():
            settings[row['key']] = row['value']
        
        return settings
    
    # === Методы для отслеживаемых пользователей ===
    
    def add_monitored_user(self, fid: int, username: str):
        """Добавить пользователя для мониторинга"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO monitored_users (fid, username) VALUES (?, ?)',
            (fid, username)
        )
        self.conn.commit()
        logger.info(f"✅ User added to monitoring: {username} (FID: {fid})")
    
    def remove_monitored_user(self, fid: int):
        """Удалить пользователя из мониторинга"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM monitored_users WHERE fid = ?', (fid,))
        self.conn.commit()
        logger.info(f"✅ User removed from monitoring: FID {fid}")
    
    def get_monitored_users(self) -> List[Dict]:
        """Получить список всех отслеживаемых пользователей"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT fid, username, added_at FROM monitored_users')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'fid': row['fid'],
                'username': row['username'],
                'added_at': row['added_at']
            })
        
        return users
    
    def user_is_monitored(self, fid: int) -> bool:
        """Проверить, отслеживается ли пользователь"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM monitored_users WHERE fid = ?', (fid,))
        return cursor.fetchone() is not None
    
    # === Методы для кастов ===
    
    def save_cast(self, cast_hash: str, fid: int, text: str, timestamp: str):
        """Сохранить информацию о касте"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO casts (hash, fid, text, timestamp) VALUES (?, ?, ?, ?)',
            (cast_hash, fid, text, timestamp)
        )
        self.conn.commit()
        logger.debug(f"✅ Cast saved: {cast_hash[:10]}...")
    
    def cast_exists(self, cast_hash: str) -> bool:
        """Проверить, существует ли каст в базе"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM casts WHERE hash = ?', (cast_hash,))
        return cursor.fetchone() is not None
    
    def get_user_casts(self, fid: int, limit: int = 50) -> List[Dict]:
        """Получить касты пользователя из базы"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT hash, text, timestamp, created_at FROM casts WHERE fid = ? ORDER BY timestamp DESC LIMIT ?',
            (fid, limit)
        )
        
        casts = []
        for row in cursor.fetchall():
            casts.append({
                'hash': row['hash'],
                'text': row['text'],
                'timestamp': row['timestamp'],
                'created_at': row['created_at']
            })
        
        return casts
    
    def get_total_casts_count(self) -> int:
        """Получить общее количество сохранённых кастов"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM casts')
        result = cursor.fetchone()
        return result['count'] if result else 0
    
    def close(self):
        """Закрыть соединение с базой данных"""
        if self.conn:
            self.conn.close()
            logger.info("✅ Database connection closed")