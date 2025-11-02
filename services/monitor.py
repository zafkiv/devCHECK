# services/monitor.py
import asyncio
import logging
from datetime import datetime
from typing import Optional
import html

from aiogram import Bot

from .database import DatabaseService
from .neynar import NeynarService

logger = logging.getLogger(__name__)


class MonitorService:
    """Сервис мониторинга новых кастов пользователей"""
    
    def __init__(
        self,
        db: DatabaseService,
        neynar: NeynarService,
        bot: Bot,
        check_interval: int = 60
    ):
        self.db = db
        self.neynar = neynar
        self.bot = bot
        self.check_interval = check_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.first_run = True  # Флаг первого запуска
        
        logger.info(f"✅ MonitorService initialized (interval: {check_interval}s)")
    
    async def start(self):
        """Запуск мониторинга"""
        if self.is_running:
            logger.warning("⚠️ Monitor service is already running")
            return
        
        self.is_running = True
        logger.info(f"🚀 Monitor service started (interval: {self.check_interval}s)")
        
        while self.is_running:
            try:
                await self._check_new_casts()
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}", exc_info=True)
            
            # Ждём перед следующей проверкой
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """Остановка мониторинга"""
        logger.info("🛑 Stopping monitor service...")
        self.is_running = False
    
    async def _check_new_casts(self):
        """Проверка новых кастов для всех отслеживаемых пользователей"""
        users = self.db.get_monitored_users()
        
        if not users:
            logger.debug("📭 No users to monitor")
            return
        
        logger.info(f"🔍 Checking {len(users)} users for new casts...")
        
        for user in users:
            try:
                await self._check_user_casts(user['fid'], user['username'])
            except Exception as e:
                logger.error(f"❌ Error checking user {user['fid']}: {e}")
        
        # После первой проверки отключаем флаг первого запуска
        if self.first_run:
            self.first_run = False
            logger.info("✅ Initial sync complete. Now monitoring in real-time mode.")
    
    async def _check_user_casts(self, fid: int, username: str):
        """Проверка новых кастов конкретного пользователя"""
        # Получаем последние касты пользователя
        casts = await self.neynar.get_user_casts(fid, limit=10)
        
        if not casts:
            logger.debug(f"📭 No casts found for user {fid}")
            return
        
        # Проверяем каждый каст
        new_casts_count = 0
        for cast in casts:
            cast_hash = cast['hash']
            
            # Проверяем, есть ли этот каст в БД
            if not self.db.cast_exists(cast_hash):
                # Сохраняем каст в БД
                self.db.save_cast(
                    cast_hash=cast_hash,
                    fid=fid,
                    text=cast['text'],
                    timestamp=cast['timestamp']
                )
                
                # Отправляем уведомление ТОЛЬКО если это не первый запуск
                if not self.first_run:
                    await self._send_notification(fid, username, cast)
                    new_casts_count += 1
        
        if new_casts_count > 0:
            logger.info(f"✅ Found {new_casts_count} new casts for @{username}")
        elif not self.first_run:
            logger.debug(f"📭 No new casts for @{username}")
    
    async def _send_notification(self, fid: int, username: str, cast: dict):
        """Отправка уведомления о новом касте"""
        settings = self.db.get_bot_settings()
        alert_group_id = settings.get('alert_group_id')
        
        if not alert_group_id:
            logger.warning("⚠️ Alert group not configured, skipping notification")
            return
        
        # Экранируем HTML-специальные символы
        text = html.escape(cast['text'][:500])  # Ограничиваем длину и экранируем
        cast_url = f"https://warpcast.com/{username}/{cast['hash'][:10]}"
        
        message = (
            f"🆕 <b>Новый каст от @{username}</b>\n\n"
            f"{text}\n\n"
            f"🔗 <a href='{cast_url}'>Открыть в Warpcast</a>"
        )
        
        try:
            await self.bot.send_message(
                chat_id=alert_group_id,
                text=message,
                disable_web_page_preview=False
            )
            logger.info(f"📨 Notification sent for cast {cast['hash'][:10]}")
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")