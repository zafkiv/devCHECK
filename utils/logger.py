import logging
import sys
from pathlib import Path


def setup_logger(log_level: str = "INFO"):
    """Настройка логирования"""
    
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Формат логов
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Основной логгер
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Файл для всех логов
    file_handler = logging.FileHandler(log_dir / "bot.log", encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # Файл только для ошибок
    error_handler = logging.FileHandler(log_dir / "errors.log", encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    logger.addHandler(error_handler)
    
    # Отключаем логи aiogram по умолчанию (слишком много)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    
    return logger