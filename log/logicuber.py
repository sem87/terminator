import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Создаем базовую папку
Path("log/logs").mkdir(exist_ok=True)


def setup_logger(name: str, log_file: str, console_level=logging.INFO,
                 max_bytes=1 * 1024 * 1024, backup_count=1):
    """Настройка логгера с ротацией по размеру.
    :param max_bytes: Максимальный размер файла (5 МБ).
    :param backup_count: Количество хранимых старых файлов (итого 3 файла по 5 МБ)."""
    logger = logging.getLogger(name)
    # <-- ИЗМЕНЕНО 3: Очищаем старые настройки, чтобы применились новые
    if logger.hasHandlers():
        logger.handlers.clear()
    # Имя логов
    logger.setLevel(logging.DEBUG)
    # Иерархия уровней логирования (числовой вес)
    # Чем выше число, тем критичнее событие:
    #     DEBUG (10) — отладка (расчеты, сырые данные).
    #     INFO (20) — штатная работа (ордер исполнен).
    #     WARNING (30) — предупреждение (задержка API, проскальзывание).
    #     ERROR (40) — ошибка (не удалось отправить запрос).
    #     CRITICAL (50) — авария (потеря связи, маржин-колл).

    # Формат: Время | Уровень | Имя логгера | Сообщение
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    # file_handler = logging.FileHandler(log_file, mode='w', encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # # Избегаем дублирования, если логгер уже настроен
    # if not logger.handlers:
    #     logger.addHandler(file_handler)
    #     logger.addHandler(console_handler)

    return logger





# --- Инициализация логгеров для торгового робота ---

# 1. Логгер сделок (в консоль только INFO и выше)
trade_log = setup_logger("Trade", "log/logs/trade.log", console_level=logging.INFO,max_bytes=500*200,backup_count=3)  # строк*байт в одной строке

# 2. Системный логгер (ошибки, аварии, варнинги)
system_log = setup_logger("System", "log/logs/system.log", console_level=logging.WARNING)

# 3. Отладочный логгер (в консоль не выводим, чтобы не спамить, только в файл)
debug_log = setup_logger("Debug", "log/logs/debug.log", console_level=logging.CRITICAL)
#
# --- Примеры использования ---
if __name__ == "__main__":
    pass
    # trade_log.info("Открыт LONG по BTCUSDT, объем 0.1")
    # system_log.warning("Задержка API Binance > 500ms")
    # system_log.critical("АВАРИЯ: Потеряно соединение с биржей! Режим остановки торгов.")
    # debug_log.debug("RSI = 34.5, MACD пересек сигнальную линию")

# import logging
# import struct
# from pathlib import Path
#
#
# class CircularFileHandler(logging.Handler):
#     """Кольцевой буфер для логов. Файл всегда весит max_bytes."""
#
#     def __init__(self, filename, max_bytes=1024 * 1024, encoding='utf-8'):
#         super().__init__()
#         self.filename = filename
#         self.max_bytes = max_bytes
#         self.encoding = encoding
#         self.header_size = 8  # 8 байт под указатель позиции (uint64)
#
#         path = Path(filename)
#         if not path.exists():
#             path.parent.mkdir(parents=True, exist_ok=True)
#             # Создаём файл фиксированного размера
#             with open(filename, 'wb') as f:
#                 f.write(b'\x00' * self.header_size)  # Заголовок (offset = 0)
#                 f.write(b' ' * (max_bytes - self.header_size))  # Тело
#
#         self.file = open(filename, 'r+b')
#         self.file.seek(0)
#         self.offset = struct.unpack('<Q', self.file.read(self.header_size))[0]
#
#         if self.offset < self.header_size or self.offset >= self.max_bytes:
#             self.offset = self.header_size
#             self._save_offset()
#
#     def _save_offset(self):
#         self.file.seek(0)
#         self.file.write(struct.pack('<Q', self.offset))
#         self.file.flush()
#
#     def emit(self, record):
#         try:
#             msg = (self.format(record) + '\n').encode(self.encoding)
#             msg_len = len(msg)
#             data_size = self.max_bytes - self.header_size
#
#             if msg_len > data_size:
#                 msg = msg[:data_size]
#                 msg_len = data_size
#
#             space_to_end = self.max_bytes - self.offset
#             if msg_len <= space_to_end:
#                 self.file.seek(self.offset)
#                 self.file.write(msg)
#                 self.offset += msg_len
#             else:
#                 self.file.seek(self.offset)
#                 self.file.write(msg[:space_to_end])
#                 self.file.seek(self.header_size)
#                 self.file.write(msg[space_to_end:])
#                 self.offset = self.header_size + (msg_len - space_to_end)
#
#             if self.offset >= self.max_bytes:
#                 self.offset = self.header_size
#
#             self._save_offset()
#             self.file.flush()
#         except Exception:
#             self.handleError(record)
#
#     def close(self):
#         if self.file:
#             self.file.close()
#         super().close()
#
#
# # Использование
# def setup_logger(name: str, log_file: str, console_level=logging.INFO, max_bytes=1024 * 1024):
#     logger = logging.getLogger(name)
#     if logger.hasHandlers():
#         logger.handlers.clear()
#
#     logger.setLevel(logging.DEBUG)
#     formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
#                                   datefmt="%Y-%m-%d %H:%M:%S")
#
#     file_handler = CircularFileHandler(log_file, max_bytes=max_bytes)
#     file_handler.setLevel(logging.DEBUG)
#     file_handler.setFormatter(formatter)
#
#     console_handler = logging.StreamHandler(sys.stdout)
#     console_handler.setLevel(console_level)
#     console_handler.setFormatter(formatter)
#
#     logger.addHandler(file_handler)
#     logger.addHandler(console_handler)
#     return logger
#
#
# trade_log = setup_logger("Trade", "log/logs/trade.log", max_bytes=1024 * 1024)  # Всегда 1 МБ