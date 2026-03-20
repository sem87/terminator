import os
import time
from datetime import datetime, timedelta
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv
from pyrogram import Client as TelegramClient
from pyrogram.enums import ParseMode

from log.logger import logger


"""ДЛЯ ЧТЕНИЯ ТОКЕНА"""
load_dotenv("../terminator/.env.term")
token = os.getenv("TOKSELL")
accid = os.getenv("AOCID")
telegtok = os.getenv("TELEGTOKENG")
groupt = os.getenv("GROUPT")
api_iddd = os.getenv("API_IDDD")
# 📦 Прокси настройки
proxy_url = os.getenv("PROXY_URL")


# ✅ Функция для преобразования строки прокси в формат Pyrogram
def get_proxy_dict(proxy_url: str | None):
    """Конвертирует proxy-строку в dict для Pyrogram"""
    if not proxy_url:
        return None
    p = urlparse(proxy_url)
    return {
        "scheme": p.scheme.lower(),
        "hostname": p.hostname,
        "port": p.port,
        "username": unquote(p.username) if p.username else None,
        "password": unquote(p.password) if p.password else None,
    }


def send_telegram(
    tupl: tuple,
    telegram_cl,
    group=groupt,
):
    """ОТПРАВЛЯЕТ В ТЕЛЕГРАММ НА ПОКУПКУ И ПРОДАЖУ"""
    # 🔍 Лог прокси
    if proxy_url := os.getenv("PROXY_URL"):
        p = urlparse(proxy_url)
        login = f"{unquote(p.username)[:2]}****:" if p.username else ""
        print(f"🌐 Прокси: {p.scheme.upper()}://{login}****@{p.hostname}:{p.port}")
    else:
        print("🌐 Прокси: ❌ не задан")
    try:
        telegram_cl.send_message(group, f"-----НАЧАЛО : {datetime.now().strftime('%d.%m.%Y %H:%M')}---")

        # 🔧 Безопасное получение ключей (если элемент — dict)
        if tupl[0]:
            keys = tupl[0].keys() if isinstance(tupl[0], dict) else [tupl[0]]
            telegram_cl.send_message(group, f"✅ ПОКУПКА : <b>{keys}</b>")
        time.sleep(1)
        if tupl[1]:
            keys = tupl[1].keys() if isinstance(tupl[1], dict) else [tupl[1]]
            telegram_cl.send_message(group, f"🔴 ПРОДАЖА : <b>{keys}</b>")

        end_time_str = (datetime.now() + timedelta(seconds=530)).strftime("%d.%m.%Y %H:%M")
        telegram_cl.send_message(group, f"-----СЛЕДУЮЩИЙ : {end_time_str}-----")
        telegram_cl.send_message(group, "🧠")
    except Exception as e:
        logger.info(f"send_telegram() ошибка в телеграмм: Ex as e : {e}")


if __name__ == "__main__":
    # 🔧 ФИКС #1: api_id как int
    # 🔧 ФИКС #2: клиент создаётся ОДИН раз вне цикла
    telegram_cl = TelegramClient(
        name="SEM",
        api_id=int(api_iddd) if api_iddd else None,  # 🔧 int!
        api_hash=telegtok,
        parse_mode=ParseMode.HTML,
        proxy=get_proxy_dict(proxy_url),
    )

    # 🔌 Подключаемся ОДИН раз перед циклом
    telegram_cl.start()
    print("✅ Подключено (постоянное соединение)")

    try:
        while True:
            tupl = ({1: 1}, {2: 2})
            # 📤 Отправляем (соединение уже есть — мгновенно)
            send_telegram(tupl=tupl, telegram_cl=telegram_cl)
            time.sleep(10)  # ⏱ пауза между итерациями
    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
    finally:
        # 🛑 Отключаемся только при завершении скрипта
        telegram_cl.stop()
        print("🔌 Отключено")
