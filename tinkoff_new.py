import os
from datetime import timedelta

from dotenv import load_dotenv
from tinkoff.invest.utils import now


# Ваш токен
"""ДЛЯ ЧТЕНИЯ ТОКЕНА"""
load_dotenv("../terminator/.env.term")  # Если файл в той же папке, что и скрипт
token = os.getenv("TOKSELL")  # Обратите внимание на имя переменной
accid = os.getenv("AOCID")  # Обратите внимание на имя переменной
telegtok = os.getenv("TELEGTOKENG")
groupt = os.getenv("GROUPT")
api_iddd = os.getenv("API_IDDD")
proxy_url = os.getenv("PROXY_URL")


def candl(cl, day: int, interval, figi: str, tiker: str):
    """ИЗВЛЕКАЕТ ДАННЫЕ ИЗ СВЕЧЕК ЗА ОПРЕДЕЛЕННЫЙ ПЕРИОД"""
    try:
        candle_data = cl.market_data.get_candles(
            figi=figi,
            from_=now() - timedelta(days=day),
            to=now(),
            interval=interval,
        )
        print(f"🕯️ Свечки для {tiker}: {len(candle_data.candles)} записей")
        return candle_data
    except Exception as e:
        print(f"❌ Ошибка свечей: {e}")
        return None


#
# def news(cl, days_back: int = 9, figi: str = None):
#     """ИЗВЛЕКАЕТ НОВОСТИ ЗА ОПРЕДЕЛЁННЫЙ ПЕРИОД"""
#     try:
#         # instruments = [{"figi": figi}] if figi else []
#         # news_response = cl.instruments.
#         # news_response = cl.news.get_news(
#         #     instruments=instruments,
#         #     from_date=now() - timedelta(days=days_back),
#         #     to_date=now()
#         # )
#
#         items = news_response.items
#         if not items:
#             print(f"📭 Новостей не найдено за {days_back} дн.")
#             return []
#
#         print(f"✅ Новостей: {len(items)}\n")
#         result = []
#
#         for news_item in items:
#             item_data = {
#                 'title': news_item.title,
#                 'url': news_item.url,
#                 'date': news_item.date,
#                 'sources': [s.name for s in news_item.sources],
#             }
#             result.append(item_data)
#             print(f"📰 {news_item.title}")
#             print(f"🔗 {news_item.url}")
#             print(f"⏰ {news_item.date}")
#             print("─" * 50)
#
#         return result
#
#     except Exception as e:
#         print(f"❌ Ошибка новостей: {e}")
#         return []

#
# # 🔥 Запуск
# if __name__ == "__main__":
#     with Client(token) as cl:  # client as cl — как вы просили
#
#         # 1. Общие новости рынка за 1 день
#         print("=== ОБЩИЕ НОВОСТИ ===")
#         general_news = news(cl, days_back=1)
#
#         # 2. Новости по конкретному инструменту (Сбербанк)
#         print("\n=== НОВОСТИ ПО СБЕРБАНКУ ===")
#         sber_figi = "BBG004730N88"
#         sber_news = news(cl, days_back=3, figi=sber_figi)
#
#         # # 3. Пример со свечками (для сравнения стиля)
#         # print("\n=== СВЕЧКИ СБЕРБАНКА ===")
#         # candles = candl(
#         #     cl,
#         #     day=1,
#         #     interval=CandleInterval.CANDLE_INTERVAL_HOUR,
#         #     figi=sber_figi,
#         #     tiker="SBER"
#         # )
