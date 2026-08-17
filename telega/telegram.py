import os
from datetime import datetime, timedelta
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

from log.logger import inform, logger


"""ДЛЯ ЧТЕНИЯ ТОКЕНА"""
load_dotenv("../terminator/.env.term")  # Если файл в той же папке, что и скрипт
token = os.getenv("TOKSELL")  # Обратите внимание на имя переменной
accid = os.getenv("AOCID")  # Обратите внимание на имя переменной
telegtok = os.getenv("TELEGTOKENG")
groupt = os.getenv("GROUPT")
api_iddd = os.getenv("API_IDDD")
proxy_url = os.getenv("PROXY_URL")


class TelegramOtpravka:
    """ВСЕ ДЛЯ ОТПРАВКИ В ТЕЛЕГРАММ"""

    def __init__(self):
        pass

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

    def send_telegram(tupl: tuple, telegram_cl, group=groupt):  # , buy_day=buy_day
        """ОТПРАВЛЯЕТ В ТЕЛЕГРАММ НА ПОКУПКУ И ПРОДАЖУ"""
        # 🔍 Лог прокси
        if proxy_url := os.getenv("PROXY_URL"):
            p = urlparse(proxy_url)
            login = f"{unquote(p.username)[:2]}****:" if p.username else ""
            inform.info(f"Прокси: {p.scheme.upper()}://{login}****@{p.hostname}:{p.port}")
        else:
            inform.info("Прокси: не задан !!!send_telegram()")
        try:
            telegram_cl.send_message(group, f"-----НАЧАЛО : {datetime.now().strftime('%d.%m.%Y %H:%M')}---")

            # # 🔧 Безопасное получение ключей (если элемент — dict)
            # if tupl[0]:
            #     keys = tupl[0].keys() if isinstance(tupl[0], dict) else [tupl[0]]
            #     telegram_cl.send_message(group, f"✅ ПОКУПКА : <b>{keys}</b>")
            # telegram_cl.send_message(group, f"ДЕНЬ ВВЕРХ <b>{buy_day.keys()}</b>")
            # telegram_cl.send_message(group, f"ДЕНЬ ВНИЗ <b>{sale_day.keys()}</b>")
            # time.sleep(1)
            # if tupl[1]:
            #     keys = tupl[1].keys() if isinstance(tupl[1], dict) else [tupl[1]]
            #     telegram_cl.send_message(group, f"🔴 ПРОДАЖА : <b>{keys}</b>")
            end_time_str = (datetime.now() + timedelta(seconds=530)).strftime("%d.%m.%Y %H:%M")
            telegram_cl.send_message(group, f"-----СЛЕДУЮЩИЙ : {end_time_str}-----")
            telegram_cl.send_message(group, "🧠")
        except Exception as e:
            logger.info(f"send_telegram() ошибка в телеграмм: Ex as e : {e}")

    # -------КОНЕЦ ОТПРАВКА В ТЕЛЕГРАММ--------


if __name__ == "__main__":
    # # НАЧАЛО------ПРОВЕРКА ОБНОВЛЕНИЯ tiker_figi.json-------
    # with Client(token) as cl:
    #     last_modified_json(cl=cl)
    # # КОНЕЦ------ПРОВЕРКА ОБНОВЛЕНИЯ tiker_figi.json-------
    # # НАЧАЛО------СОЗДАЕМ TelegramClient------
    # telegram_cl = TelegramClient(
    #     name="SEM",
    #     api_id=int(api_iddd) if api_iddd else None,  # 🔧 int!
    #     api_hash=telegtok,
    #     parse_mode=ParseMode.HTML,
    #     proxy=get_proxy_dict(proxy_url),
    # )
    #
    # # Подключаемся ОДИН раз перед циклом
    # telegram_cl.start()
    pass
