# handlers/admin.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    await message.answer(
        "👋 <b>Добро пожаловать в Farcaster Monitor Bot!</b>\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "/start - Показать это сообщение\n"
        "/setadmin - Установить себя как админа\n"
        "/setgroup [ID] - Установить группу для уведомлений\n"
        "/add [FID] - Добавить пользователя для мониторинга\n"
        "/remove [FID] - Удалить пользователя из мониторинга\n"
        "/list - Показать список отслеживаемых пользователей\n"
        "/stats - Показать статистику\n"
        "/help - Показать помощь"
    )


@router.message(Command("setadmin"))
async def cmd_set_admin(message: Message, db):
    """Установить админа"""
    try:
        db.set_admin_user(message.from_user.id)
        await message.answer(
            f"✅ Вы назначены администратором!\n"
            f"👤 User ID: <code>{message.from_user.id}</code>"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("setgroup"))
async def cmd_set_group(message: Message, db):
    """Установить группу для уведомлений"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "❌ Укажите ID группы!\n"
            "Пример: <code>/setgroup -100XXXXXXXXXX</code>"
        )
        return
    
    try:
        group_id = int(args[1])
        db.set_alert_group(group_id)
        await message.answer(
            f"✅ Группа для уведомлений установлена!\n"
            f"📢 Group ID: <code>{group_id}</code>"
        )
    except ValueError:
        await message.answer("❌ ID группы должен быть числом!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Показать помощь"""
    await message.answer(
        "📖 <b>Справка по командам:</b>\n\n"
        "<b>/setadmin</b> - Установить себя как администратора бота\n\n"
        "<b>/setgroup [ID]</b> - Установить группу для отправки уведомлений\n"
        "Пример: <code>/setgroup -100XXXXXXXXXX</code>\n\n"
        "<b>/add [FID]</b> - Добавить пользователя Farcaster для мониторинга\n"
        "Пример: <code>/add 3</code>\n\n"
        "<b>/remove [FID]</b> - Удалить пользователя из мониторинга\n"
        "Пример: <code>/remove 3</code>\n\n"
        "<b>/list</b> - Показать всех отслеживаемых пользователей\n\n"
        "<b>/stats</b> - Показать статистику бота"
    )
