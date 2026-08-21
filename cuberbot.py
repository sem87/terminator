# from telega.telegram import TelegramOtpravka
import time

from actualnost_ticker.actualnost import ReadTickerFigiJson
from sbor_dannih.sbor_dannih import SborDannih
from t_tech.invest import CandleInterval, Client

if __name__ == "__main__":
    # ==========НАЧАЛО РОБОТЫ С JSON и подготовка работы с актуальными тикерами и их FIGI. ============
    # with ActualniiTiker(days=5) as actual_tiker:
    #     # Проверяем актуальность
    #     actual_tiker.last_modified_json()
    # =========================================
    # Можно узнать тикер по фиги
    # print(actual_tiker.get_figi(tiker="TGLD@"))
    # Можно вытащить из базы sql_terminator все "на рынке"
    # actual_tiker.list_active_tickers()
    # Можно прочитать read_tiker_figi_json()
    # print(actual_tiker.read_tiker_figi_json())
    # ==========================================
    # ==========КОНЕЦ РОБОТЫ С JSON и подготовка работы с актуальными тикерами и их FIGI. ============
    # ==========НАЧАЛО РОБОТЫ С ТЕЛЕГРАМ ============
    # # Класс сам запустит (start) и закроет (stop) клиент
    # with TelegramOtpravka() as tg:
    #     # test_data = [{"BTC": 100}, {"ETH": 200}]
    #     tg.send_telegram(tupl="test_data")
    # ==========КОНЕЦ РОБОТЫ С ТЕЛЕГРАМ============
    # ==========НАЧАЛО СБОР ДАННЫХ===========
    while True:
        with SborDannih() as sbor_dannich:
            for tiker, figi in ReadTickerFigiJson().read_tiker_figi_json().items():
                print(f"Тикер - {tiker},фиги - {figi}")
                print(sbor_dannich.candl(day=1,interval=CandleInterval.CANDLE_INTERVAL_HOUR, figi=figi, tiker=figi))
        time.sleep(10)


    # while True:
    #     with SborDannih() as sbor:
    #         print(sbor)
    #     time.sleep(10)

    # ==========КОНЕЦ СБОР ДАННЫХ============
