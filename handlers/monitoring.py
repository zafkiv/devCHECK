# handlers/monitoring.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("add"))
async def cmd_add_user(message: Message, db, neynar):
    """Добавить пользователя для мониторинга"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "❌ Укажите FID пользователя!\n"
            "Пример: <code>/add 3</code>"
        )
        return
    
    try:
        fid = int(args[1])
        
        # Получаем информацию о пользователе из Neynar
        user_info = await neynar.get_user_by_fid(fid)
        
        if not user_info:
            await message.answer(f"❌ Пользователь с FID {fid} не найден!")
            return
        
        # Добавляем в БД
        db.add_monitored_user(fid, user_info['username'])
        
        await message.answer(
            f"✅ Пользователь добавлен в мониторинг!\n\n"
            f"👤 FID: <code>{fid}</code>\n"
            f"📛 Username: @{user_info['username']}\n"
            f"🔗 Profile: https://warpcast.com/{user_info['username']}"
        )
    except ValueError:
        await message.answer("❌ FID должен быть числом!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("remove"))
async def cmd_remove_user(message: Message, db):
    """Удалить пользователя из мониторинга"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "❌ Укажите FID пользователя!\n"
            "Пример: <code>/remove 3</code>"
        )
        return
    
    try:
        fid = int(args[1])
        db.remove_monitored_user(fid)
        
        await message.answer(
            f"✅ Пользователь удалён из мониторинга!\n"
            f"👤 FID: <code>{fid}</code>"
        )
    except ValueError:
        await message.answer("❌ FID должен быть числом!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("list"))
async def cmd_list_users(message: Message, db):
    """Показать список отслеживаемых пользователей"""
    try:
        users = db.get_monitored_users()
        
        if not users:
            await message.answer("📭 Список отслеживаемых пользователей пуст")
            return
        
        text = "👥 <b>Отслеживаемые пользователи:</b>\n\n"
        
        for user in users:
            text += (
                f"👤 FID: <code>{user['fid']}</code>\n"
                f"📛 Username: @{user['username']}\n"
                f"🔗 <a href='https://warpcast.com/{user['username']}'>Профиль</a>\n"
                f"➖➖➖➖➖➖➖➖➖➖\n"
            )
        
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("stats"))
async def cmd_stats(message: Message, db):
    """Показать статистику"""
    try:
        settings = db.get_bot_settings()
        users = db.get_monitored_users()
        
        text = (
            "📊 <b>Статистика бота:</b>\n\n"
            f"👥 Отслеживаемых пользователей: <b>{len(users)}</b>\n"
            f"👤 Админ ID: <code>{settings.get('admin_user_id', 'Не установлен')}</code>\n"
            f"📢 Группа уведомлений: <code>{settings.get('alert_group_id', 'Не установлена')}</code>\n"
        )
        
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")