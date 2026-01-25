from utils import *


def send_telegram_log_db(
        telegram_cl=TelegramClient(name="SEM", api_id=api_iddd, api_hash=telegtok, parse_mode=ParseMode.HTML),
        group=groupt):
    """ОТПРАВЛЯЕТ В ТЕЛЕГРАММ ЛОГИ И БАЗУ ДАННЫХ"""
    try:
        with telegram_cl:
            telegram_cl.send_message(group, f"✌️")
            telegram_cl.send_document(chat_id=group, document="sql_terminator.db",
                                      caption="Файл базы данных")
            time.sleep(2)
            telegram_cl.send_document(chat_id=group, document="log/informing/inform.log",
                                      caption="Информ лог")
            time.sleep(2)
            telegram_cl.send_document(chat_id=group, document="log/logs/loGgGi.log",
                                      caption="Информ лог")
    except Exception as e:
        logger.info(f"send_telegram_log_db ошибка в телеграмм логи и база: Ex as e : {e}")


if __name__ == "__main__":
    send_telegram_log_db()
