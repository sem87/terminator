import os
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv
from pyrogram import Client as TelegramClient
from pyrogram.enums import ParseMode

from log.logger import inform


# Загружаем переменные окружения один раз при импорте
load_dotenv("../terminator/.env.term")


class TelegramOtpravka:
    """Класс для отправки сообщений в Telegram через Pyrogram."""

    def __init__(self):
        self.api_id = int(os.getenv("API_IDDD", 0))
        self.api_hash = os.getenv("TELEGTOKENG", "")
        self.group = os.getenv("GROUPT", "")
        self.proxy_url = os.getenv("PROXY_URL")

        self.client = TelegramClient(
            name="SEM",
            api_id=self.api_id,
            api_hash=self.api_hash,
            parse_mode=ParseMode.HTML,
            proxy=self._get_proxy_dict(self.proxy_url),
        )

    @staticmethod
    def _get_proxy_dict(proxy_url: str | None) -> dict | None:
        """Конвертирует proxy-строку в dict для Pyrogram."""
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

    def start(self):
        """Запускает клиент и логирует прокси."""
        if self.proxy_url:
            p = urlparse(self.proxy_url)
            login = f"{unquote(p.username)[:2]}****:" if p.username else ""
            inform.info(f"Прокси: {p.scheme.upper()}://{login}****@{p.hostname}:{p.port}")
        else:
            inform.info("Прокси: не задан")

        self.client.start()

    def stop(self):
        """Корректно останавливает клиент."""
        if self.client.is_connected:
            self.client.stop()

    def send_telegram(self, tupl: tuple[Any, Any]):
        """Отправляет сообщение о покупке/продаже в Telegram."""
        try:
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            end_time_str = (datetime.now() + timedelta(seconds=530)).strftime("%d.%m.%Y %H:%M")

            self.client.send_message(self.group, f"-----НАЧАЛО : {now_str}---")

            # Пример обработки данных (раскомментируйте при необходимости)
            if tupl:
                keys = tupl.keys() if isinstance(tupl, dict) else [tupl]
                self.client.send_message(self.group, f"✅ ПОКУПКА : <b>{keys}</b>")

            self.client.send_message(self.group, f"-----СЛЕДУЮЩИЙ : {end_time_str}-----")
            self.client.send_message(self.group, "🧠")

        except Exception as e:
            inform.info(f"Ошибка отправки в Telegram: {e}")

    def __enter__(self):
        """Поддержка контекстного менеджера (with)."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие при выходе из блока with."""
        self.stop()


if __name__ == "__main__":
    # # Класс сам запустит (start) и закроет (stop) клиент
    # with TelegramOtpravka() as tg:
    #     test_data = ({"BTC": 100}, {"ETH": 200})
    #     tg.send_telegram(test_data)
    pass
