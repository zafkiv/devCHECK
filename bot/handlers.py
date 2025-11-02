import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from services.database import DatabaseService
from services.neynar import NeynarService

logger = logging.getLogger(__name__)
router = Router()


class BotHandlers:
    """Обработчики команд бота"""
    
    def __init__(self, db: DatabaseService, neynar: NeynarService):
        self.db = db
        self.neynar = neynar
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        admin_id = await self.db.get_admin_user()
        
        # Если админ не установлен, первый пользователь становится админом
        if admin_id is None:
            await self.db.set_admin_user(user_id)
            return True
        
        return user_id == admin_id
    
    async def cmd_start(self, message: Message):
        """Команда /start"""
        user_id = message.from_user.id
        is_admin = await self.is_admin(user_id)
        
        text = "👋 <b>Farcaster Monitor Bot</b>\n\n"
        
        if is_admin:
            text += "🔑 Вы администратор бота\n\n"
            text += "<b>Команды управления FID:</b>\n"
            text += "/add &lt;FID&gt; - Добавить FID для отслеживания\n"
            text += "/remove &lt;FID&gt; - Удалить FID\n"
            text += "/pause &lt;FID&gt; - Приостановить отслеживание\n"
            text += "/resume &lt;FID&gt; - Возобновить отслеживание\n"
            text += "/list - Показать все отслеживаемые FID\n\n"
            
            text += "<b>Настройка группы для алертов:</b>\n"
            text += "/setgroup - Установить текущую группу для алертов\n"
            text += "/getid - Узнать ID текущего чата/группы\n"
            text += "/checkgroup - Проверить настройку группы алертов\n\n"
            
            text += "<b>Управление ботом:</b>\n"
            text += "/stats - Статистика\n"
            text += "/help - Подробная справка\n\n"
            
            settings = await self.db.get_bot_settings()
            if settings.alert_group_id:
                text += f"✅ Группа для алертов: <code>{settings.alert_group_id}</code>\n"
            else:
                text += "⚠️ Группа для алертов не настроена. Используйте /setgroup\n"
        else:
            text += "У вас нет прав администратора.\n"
            text += "Обратитесь к владельцу бота."
        
        await message.answer(text)
    
    async def cmd_getid(self, message: Message):
        """Команда /getid - Узнать ID чата"""
        chat_id = message.chat.id
        chat_type = message.chat.type
        chat_title = getattr(message.chat, 'title', None)
        
        text = "🆔 <b>Информация о чате:</b>\n\n"
        text += f"ID: <code>{chat_id}</code>\n"
        text += f"Тип: {chat_type}\n"
        
        if chat_title:
            text += f"Название: {chat_title}\n"
        
        text += f"\n💡 Скопируйте ID и используйте команду:\n"
        text += f"<code>/setgroup {chat_id}</code>"
        
        await message.answer(text)
    
    async def cmd_setgroup(self, message: Message):
        """Команда /setgroup - Установить группу для алертов"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("❌ Только администратор может выполнить эту команду")
            return
        
        args = message.text.split(maxsplit=1)
        
        # Если ID не указан, используем текущий чат
        if len(args) > 1:
            try:
                group_id = int(args[1])
            except ValueError:
                await message.answer("❌ ID группы должен быть числом")
                return
        else:
            group_id = message.chat.id
            
            # Проверяем, что это группа
            if message.chat.type not in ['group', 'supergroup']:
                await message.answer(
                    "❌ Эта команда должна быть выполнена в группе\n\n"
                    "Или укажите ID группы: /setgroup &lt;ID&gt;"
                )
                return
        
        try:
            # Пробуем отправить тестовое сообщение
            await message.bot.send_message(
                chat_id=group_id,
                text="✅ Эта группа успешно настроена для получения алертов о кастах"
            )
            
            await self.db.set_alert_group(group_id)
            
            await message.answer(
                f"✅ Группа для алертов установлена\n"
                f"ID: <code>{group_id}</code>\n\n"
                f"Все новые касты будут отправляться в эту группу."
            )
        except Exception as e:
            await message.answer(
                f"❌ Не удалось отправить сообщение в группу {group_id}\n\n"
                f"Убедитесь, что:\n"
                f"1. Бот добавлен в группу\n"
                f"2. У бота есть права на отправку сообщений\n"
                f"3. ID группы указан верно\n\n"
                f"Ошибка: {str(e)}"
            )
    
    async def cmd_checkgroup(self, message: Message):
        """Команда /checkgroup - Проверить группу"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("❌ Только администратор может выполнить эту команду")
            return
        
        group_id = await self.db.get_alert_group()
        
        if not group_id:
            await message.answer(
                "⚠️ Группа для алертов не настроена\n\n"
                "Используйте /setgroup для настройки"
            )
            return
        
        try:
            chat = await message.bot.get_chat(group_id)
            
            text = "✅ <b>Группа для алертов настроена:</b>\n\n"
            text += f"ID: <code>{group_id}</code>\n"
            text += f"Тип: {chat.type}\n"
            
            if hasattr(chat, 'title'):
                text += f"Название: {chat.title}\n"
            
            # Отправляем тестовое сообщение
            await message.bot.send_message(
                chat_id=group_id,
                text="🧪 Тестовое сообщение - группа работает корректно"
            )
            
            text += "\n✅ Тестовое сообщение отправлено"
            
            await message.answer(text)
            
        except Exception as e:
            await message.answer(
                f"❌ Ошибка при проверке группы {group_id}\n\n"
                f"Возможные причины:\n"
                f"1. Бот был удален из группы\n"
                f"2. У бота нет прав\n"
                f"3. Группа была удалена\n\n"
                f"Используйте /setgroup для повторной настройки\n\n"
                f"Ошибка: {str(e)}"
            )
    
    async def cmd_add(self, message: Message):
        """Команда /add <FID>"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("❌ Только администратор может добавлять FID")
            return
        
        args = message.text.split()
        
        if len(args) < 2:
            await message.answer(
                "❌ Укажите FID\n\n"
                "<b>Пример:</b> /add 3\n\n"
                "<b>Как найти FID:</b>\n"
                "1. Откройте профиль на Warpcast\n"
                "2. FID указан в URL или профиле"
            )
            return
        
        try:
            fid = int(args[1])
            if fid <= 0:
                raise ValueError()
        except ValueError:
            await message.answer("❌ FID должен быть положительным числом")
            return
        
        try:
            await message.answer("🔍 Проверяю пользователя...")
            
            # Получаем информацию о пользователе (синхронный вызов)
            import asyncio
            loop = asyncio.get_event_loop()
            user = await loop.run_in_executor(
                None,
                self.neynar.get_user_by_fid,
                fid
            )
            
            if not user:
                await message.answer(f"❌ Пользователь с FID {fid} не найден")
                return
            
            await self.db.add_fid(fid, user.get('username'))
            
            text = "✅ <b>FID добавлен в мониторинг</b>\n\n"
            text += f"FID: <code>{fid}</code>\n"
            text += f"Username: @{user.get('username')}\n"
            text += f"Display Name: {user.get('display_name')}\n"
            text += f"Подписчиков: {user.get('follower_count', 0)}\n"
            text += f"Подписок: {user.get('following_count', 0)}\n\n"
            
            group_id = await self.db.get_alert_group()
            if group_id:
                text += "📢 Новые касты будут отправляться в группу"
            else:
                text += "⚠️ Не забудьте настроить группу для алертов: /setgroup"
            
            await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error adding FID: {e}", exc_info=True)
            await message.answer(f"❌ Ошибка: {str(e)}")
    
    async def cmd_remove(self, message: Message):
        """Команда /remove <FID>"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("❌ Только администратор может удалять FID")
            return
        
        args = message.text.split()
        
        if len(args) < 2:
            await message.answer("❌ Укажите FID\nПример: /remove 3")
            return
        
        try:
            fid = int(args[1])
        except ValueError:
            await message.answer("❌ FID должен быть числом")
            return
        
        removed = await self.db.remove_fid(fid)
        
        if removed:
            await message.answer(f"✅ FID {fid} удален из мониторинга")
        else:
            await message.answer(f"❌ FID {fid} не найден в списке отслеживания")
    
    async def cmd_pause(self, message: Message):
        """Команда /pause <FID>"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("❌ Только администратор может приостанавливать мониторинг")
            return
        
        args = message.text.split()
        
        if len(args) < 2:
            await message.answer("❌ Укажите FID\nПример: /pause 3")
            return
        
        try:
            fid = int(args[1])
        except ValueError:
            await message.answer("❌ FID должен быть числом")
            return
        
        updated = await self.db.toggle_fid(fid, False)
        
        if updated:
            await message.answer(f"⏸ FID {fid} приостановлен\nДля возобновления: /resume {fid}")
        else:
            await message.answer(f"❌ FID {fid} не найден")
    
    async def cmd_resume(self, message: Message):
        """Команда /resume <FID>"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("❌ Только администратор может возобновлять мониторинг")
            return
        
        args = message.text.split()
        
        if len(args) < 2:
            await message.answer("❌ Укажите FID\nПример: /resume 3")
            return
        
        try:
            fid = int(args[1])
        except ValueError:
            await message.answer("❌ FID должен быть числом")
            return
        
        updated = await self.db.toggle_fid(fid, True)
        
        if updated:
            await message.answer(f"▶️ FID {fid} возобновлен")
        else:
            await message.answer(f"❌ FID {fid} не найден")
    
    async def cmd_list(self, message: Message):
        """Команда /list"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("❌ Только администратор может просматривать список")
            return
        
        fids = await self.db.get_all_monitored_fids(only_active=False)
        
        if not fids:
            await message.answer(
                "📭 <b>Нет отслеживаемых FID</b>\n\n"
                "Используйте /add &lt;FID&gt; для добавления"
            )
            return
        
        active_fids = [f for f in fids if f.is_active]
        paused_fids = [f for f in fids if not f.is_active]
        
        text = f"📊 <b>Отслеживаемые FID ({len(fids)})</b>\n\n"
        
        if active_fids:
            text += f"<b>✅ Активные ({len(active_fids)}):</b>\n"
            for entry in active_fids:
                username = entry.username or 'unknown'
                profile_link = f"https://warpcast.com/{username}"
                
                text += f"• <a href=\"{profile_link}\">{entry.fid}</a> - @{username}"
                
                if entry.last_checked:
                    time_ago = self._get_time_ago(entry.last_checked)
                    text += f" ({time_ago})"
                
                text += "\n"
            text += "\n"
        
        if paused_fids:
            text += f"<b>⏸ Приостановлено ({len(paused_fids)}):</b>\n"
            for entry in paused_fids:
                username = entry.username or 'unknown'
                text += f"• {entry.fid} - @{username}\n"
            text += "\n"
        
        text += "\n<b>Команды:</b>\n"
        text += "/add &lt;FID&gt; - добавить\n"
        text += "/remove &lt;FID&gt; - удалить\n"
        text += "/pause &lt;FID&gt; - приостановить\n"
        text += "/resume &lt;FID&gt; - возобновить"
        
        await message.answer(text, disable_web_page_preview=True)
    
    async def cmd_stats(self, message: Message):
        """Команда /stats"""
        if not await self.is_admin(message.from_user.id):
            await message.answer("❌ Только администратор может просматривать статистику")
            return
        
        stats = await self.db.get_stats()
        settings = await self.db.get_bot_settings()
        
        text = "📈 <b>Статистика бота</b>\n\n"
        
        text += "<b>Мониторинг:</b>\n"
        text += f"• Всего FID: {stats['total_fids']}\n"
        text += f"• Активных: {stats['active_fids']}\n"
        text += f"• Приостановлено: {stats['total_fids'] - stats['active_fids']}\n"
        text += f"• Отправлено кастов: {stats['total_casts_sent']}\n"
        
        if stats.get('oldest_monitored'):
            days = (datetime.now() - stats['oldest_monitored']).days
            text += f"• Работает: {days} дней\n"
        
        text += "\n<b>Настройки:</b>\n"
        text += f"• Бот: {'✅ Активен' if settings.is_active else '⏸ Приостановлен'}\n"
        text += f"• Группа алертов: {'✅ ' + str(settings.alert_group_id) if settings.alert_group_id else '❌ Не настроена'}\n"
        
        import os
        interval = os.getenv('POLL_INTERVAL_SECONDS', '60')
        text += f"• Интервал проверки: {interval}с\n"
        
        await message.answer(text)
    
    async def cmd_help(self, message: Message):
        """Команда /help"""
        is_admin = await self.is_admin(message.from_user.id)
        
        text = "📖 <b>Справка Farcaster Monitor Bot</b>\n\n"
        
        if is_admin:
            text += "<b>🔧 Первоначальная настройка:</b>\n"
            text += "1. Добавьте бота в группу для алертов\n"
            text += "2. В группе выполните /getid\n"
            text += "3. Скопируйте ID и выполните /setgroup\n"
            text += "4. Добавьте FID командой /add\n\n"
            
            text += "<b>👥 Управление FID:</b>\n"
            text += "/add &lt;FID&gt; - добавить FID для мониторинга\n"
            text += "/remove &lt;FID&gt; - удалить FID\n"
            text += "/pause &lt;FID&gt; - временно отключить\n"
            text += "/resume &lt;FID&gt; - включить обратно\n"
            text += "/list - показать все FID\n\n"
            
            text += "<b>⚙️ Настройки:</b>\n"
            text += "/setgroup [ID] - установить группу для алертов\n"
            text += "/getid - узнать ID текущего чата\n"
            text += "/checkgroup - проверить группу алертов\n\n"
            
            text += "<b>📊 Информация:</b>\n"
            text += "/stats - статистика работы\n"
            text += "/help - эта справка\n\n"
            
            text += "<b>💡 Примеры FID:</b>\n"
            text += "• 3 - dwr.eth (основатель Farcaster)\n"
            text += "• 2 - v (Vitalik Buterin)\n"
            text += "• 1 - farcaster (официальный)\n\n"
            
            text += "<b>🔍 Как найти FID:</b>\n"
            text += "1. Откройте профиль на warpcast.com\n"
            text += "2. FID указан в URL или в профиле\n"
            text += "3. Или используйте neynar.com для поиска"
        else:
            text += "У вас нет прав администратора.\n"
            text += "Обратитесь к владельцу бота для получения доступа."
        
        await message.answer(text)
    
    @staticmethod
    def _get_time_ago(dt: datetime) -> str:
        """Получить строку 'X времени назад'"""
        delta = datetime.now() - dt
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)}с назад"
        elif seconds < 3600:
            return f"{int(seconds / 60)}м назад"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}ч назад"
        else:
            return f"{int(seconds / 86400)}д назад"


# Регистрация обработчиков
def register_handlers(router: Router, handlers: BotHandlers):
    """Регистрация всех обработчиков"""
    router.message.register(handlers.cmd_start, Command("start"))
    router.message.register(handlers.cmd_help, Command("help"))
    router.message.register(handlers.cmd_getid, Command("getid"))
    router.message.register(handlers.cmd_setgroup, Command("setgroup"))
    router.message.register(handlers.cmd_checkgroup, Command("checkgroup"))
    router.message.register(handlers.cmd_add, Command("add"))
    router.message.register(handlers.cmd_remove, Command("remove"))
    router.message.register(handlers.cmd_pause, Command("pause"))
    router.message.register(handlers.cmd_resume, Command("resume"))
    router.message.register(handlers.cmd_list, Command("list"))
    router.message.register(handlers.cmd_stats, Command("stats"))