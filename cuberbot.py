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
    # a = 0
    # while a < 1:
    #     a = a + 1
    #     with SborDannih() as sbor_dannich:
    #         for tiker, figi in ReadTickerFigiJson().read_tiker_figi_json().items():
    #             for time_list, time_list_day in [(CandleInterval.CANDLE_INTERVAL_DAY, 50),
    #                                              (CandleInterval.CANDLE_INTERVAL_HOUR, 7),
    #                                              (CandleInterval.CANDLE_INTERVAL_5_MIN, 1)]:
    #                 # (CandleInterval.CANDLE_INTERVAL_DAY.name, 50)
    #                 print(f"Тикер - {tiker},фиги - {figi} , тайм лист - {time_list} , тайм лист дней - {time_list_day}")
    #                 #print(sbor_dannich.candl(day=time_list_day,interval=time_list, figi=figi, tiker=figi))
    #                 print(sbor_dannich.calculate_indicator(
    #                     df=sbor_dannich.candl(day=time_list_day, interval=time_list, figi=figi,
    #                                           tiker=tiker), tiker=tiker).last_sma_10_1)
    #     time.sleep(10)

    # Используем while True для постоянной работы, или while a < 1, если нужен только 1 прогон
    while True:
        with SborDannih() as sbor:
            # 1. Очищаем итоговые словари перед новым кругом, чтобы не копился мусор
            sbor.buy_itog.clear()
            sbor.sale_itog.clear()

            # Получаем список тикеров
            tickers_data = ReadTickerFigiJson().read_tiker_figi_json().items()

            for tiker, figi in tickers_data:
                try:
                    print(f"⏳ Обработка: {tiker} (FIGI: {figi})")

                    # 2. Собираем и рассчитываем данные для ВСЕХ таймфреймов СРАЗУ
                    # День
                    df_day = sbor.candl(day=50, interval=CandleInterval.CANDLE_INTERVAL_DAY, figi=figi, tiker=tiker)
                    data_day = sbor.calculate_indicator(df=df_day, tiker=tiker)

                    # Час
                    df_hour = sbor.candl(day=7, interval=CandleInterval.CANDLE_INTERVAL_HOUR, figi=figi,
                                         tiker=tiker)
                    data_hour = sbor.calculate_indicator(df=df_hour, tiker=tiker)

                    # 5 минут
                    df_5min = sbor.candl(day=1, interval=CandleInterval.CANDLE_INTERVAL_5_MIN, figi=figi,
                                         tiker=tiker)
                    data_5min = sbor.calculate_indicator(df=df_5min, tiker=tiker)

                    # 3. Проверяем, что данные успешно собрались (не вернули None из-за ошибки или пустого DF)
                    if data_day and data_hour and data_5min:
                        # 4. ВЫЗЫВАЕМ ПРОВЕРКУ КОНФЛЮЕНСА!
                        sbor.check_confluence(
                            figi=figi,
                            tiker=tiker,
                            data_day=data_day,
                            data_hour=data_hour,
                            data_5min=data_5min
                        )
                    else:
                        print(f"⚠️ {tiker}: Не хватило данных для расчета индикаторов на одном из таймфреймов.")

                except Exception as e:
                    print(f"❌ Критическая ошибка при обработке {tiker}: {e}")
                    continue  # Переходим к следующему тику, не ломая весь цикл

            # 5. После прохода по ВСЕМ тикерам, выводим итоги цикла
            print("\n" + "=" * 60)
            print("📊 ИТОГИ ТЕКУЩЕГО ЦИКЛА:")

            if sbor.buy_itog:
                print(f"✅ НАЙДЕНО СИГНАЛОВ НА ПОКУПКУ: {len(sbor.buy_itog)}")
                for t, info in sbor.buy_itog.items():
                    print(f"   🟢 {t} | Стратегия: {info['strategy']}")
                    print(f"      Описание: {info['description']}")
            else:
                print("✅ Сигналов на покупку (конфлюенс 3ТФ) нет.")

            if sbor.sale_itog:
                print(f"🔻 НАЙДЕНО СИГНАЛОВ НА ПРОДАЖУ: {len(sbor.sale_itog)}")
                for t, info in sbor.sale_itog.items():
                    print(f"   🔴 {t} | Стратегия: {info['strategy']}")
                    print(f"      Описание: {info['description']}")
            else:
                print("🔻 Сигналов на продажу (конфлюенс 3ТФ) нет.")

            print("=" * 60 + "\n")

        # Ждем 10 секунд перед следующим полным кругом проверки всех тикеров
        time.sleep(10)




    # while True:
    #     with SborDannih() as sbor:
    #         print(sbor)
    #     time.sleep(10)

    # ==========КОНЕЦ СБОР ДАННЫХ============
