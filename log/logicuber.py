import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Создаем базовую папку
Path("logs").mkdir(exist_ok=True)


def setup_logger(name: str, log_file: str, console_level=logging.INFO,
                 max_bytes=1 * 1024 * 1024, backup_count=0):
    """
    Настройка логгера с ротацией по размеру.
    :param max_bytes: Максимальный размер файла (5 МБ).
    :param backup_count: Количество хранимых старых файлов (итого 3 файла по 5 МБ).
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Формат: Время | Уровень | Имя логгера | Сообщение
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # Избегаем дублирования, если логгер уже настроен
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger





# --- Инициализация логгеров для торгового робота ---

# 1. Логгер сделок (в консоль только INFO и выше)
trade_log = setup_logger("Trade", "logs/trade.log", console_level=logging.INFO)

# 2. Системный логгер (ошибки, аварии, варнинги)
system_log = setup_logger("System", "logs/system.log", console_level=logging.WARNING)

# 3. Отладочный логгер (в консоль не выводим, чтобы не спамить, только в файл)
debug_log = setup_logger("Debug", "logs/debug.log", console_level=logging.CRITICAL)
#
# --- Примеры использования ---
if __name__ == "__main__":
    trade_log.info("Открыт LONG по BTCUSDT, объем 0.1")
    system_log.warning("Задержка API Binance > 500ms")
    system_log.critical("АВАРИЯ: Потеряно соединение с биржей! Режим остановки торгов.")
    debug_log.debug("RSI = 34.5, MACD пересек сигнальную линию")