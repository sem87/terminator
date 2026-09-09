import time
from t_tech.invest import CandleInterval

from actualnost_ticker.actualnost import ReadTickerFigiJson
from log.logicuber import system_log, debug_log
from sbor_dannih.sbor_dannih import SborDannih, PrivlicatelnostChitaemost
from telega.telegram import TelegramOtpravka

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
            # 1. Очищаем итоговые словари перед новым кругом, чтобы не копился мусор
            sbor_dannich.cleaning_dict()
            # debug_log.debug(f"продажа ===== {sbor_dannich.sale_itog}")
            # debug_log.debug(f"продажа ===== {sbor_dannich.sale_itog_d_h}")
            # debug_log.debug(f"покупка ===== {sbor_dannich.buy_itog}")
            # debug_log.debug(f"покупка ===== {sbor_dannich.buy_itog_d_h}")
            # Достаем тикер и фиги из sqllite базы которые имеют статус "на рынке"
            for tiker, figi in ReadTickerFigiJson().read_tiker_figi_json().items():
                try:
                    # logger.info(f"Тикер - {tiker},фиги - {figi}")
                    # 2. Собираем и рассчитываем данные для ВСЕХ таймфреймов СРАЗУ
                    # День
                    df_day = sbor_dannich.candl(
                        day=50, interval=CandleInterval.CANDLE_INTERVAL_DAY, figi=figi, tiker=tiker
                    )
                    data_day = sbor_dannich.calculate_indicator(df=df_day, tiker=tiker)
                    # Час
                    df_hour = sbor_dannich.candl(
                        day=7, interval=CandleInterval.CANDLE_INTERVAL_HOUR, figi=figi, tiker=tiker
                    )
                    data_hour = sbor_dannich.calculate_indicator(df=df_hour, tiker=tiker)
                    # 5 минут
                    df_5min = sbor_dannich.candl(
                        day=1, interval=CandleInterval.CANDLE_INTERVAL_5_MIN, figi=figi, tiker=tiker
                    )
                    data_5min = sbor_dannich.calculate_indicator(df=df_5min, tiker=tiker)

                    # 3. Проверяем, что данные успешно собрались (не вернули None из-за ошибки или пустого DF)
                    if data_day and data_hour and data_5min:
                        # 4. ВЫЗЫВАЕМ ПРОВЕРКУ КОНФЛЮЕНСА! и записываем в словарь
                        sbor_dannich.strategy_day_hour_5min(
                            figi=figi, tiker=tiker, data_day=data_day, data_hour=data_hour, data_5min=data_5min)
                        # 5. Делаем расчет, записываем в словарь и отправляем инфу в телегу для молнии с расчетом кто привлекательнее
                        sbor_dannich.strategy_telega_day_hour(
                            figi=figi, tiker=tiker, data_day=data_day, data_hour=data_hour)
                    else:
                        system_log.critical(
                            f"{tiker}: Не хватило данных для расчета индикаторов на одном из таймфреймов.")
                except Exception as e:
                    system_log.critical(f"Крит ошибка при обработке данных cuberbot в SborDannih() - {tiker}: {e}")
                    continue  # Переходим к следующему тику, не ломая весь цикл
        debug_log.info(f"Telega покупка : {sbor_dannich.buy_itog_d_h}")
        debug_log.info(f"Telega продажа : {sbor_dannich.sale_itog_d_h}")
        debug_log.info(f"strategy_day_hour_5min покупка : {sbor_dannich.buy_itog}")
        debug_log.info(f"strategy_day_hour_5min продажа : {sbor_dannich.sale_itog}")
        # tupl = PrivlicatelnostChitaemost().format_signals_to_tuple(signals=sbor_dannich.buy_itog_d_h)
        # print(tupl)
        # debug_log.critical(f"**********{tupl}***********")
        with TelegramOtpravka() as tg:
            # перед отправкой в словарь нужно его расчитывать на удельную заинтересованность и фильтровать
            # в телегу отправлять по нужной форме
            tg.send_telegram(
                molnia_buy=PrivlicatelnostChitaemost(signals=sbor_dannich.buy_itog_d_h).format_signals_to_tuple(),
                molnia_sell=PrivlicatelnostChitaemost(signals=sbor_dannich.sale_itog_d_h,
                                                      reverse=True).format_signals_to_tuple(),
                cuber_buy=sbor_dannich.buy_itog.keys(), cuber_sell=sbor_dannich.sale_itog.values())
        # Ждем 10 секунд перед следующим полным кругом проверки всех тикеров
        time.sleep(120)

    # ==========КОНЕЦ СБОР ДАННЫХ============

    # ==========НАЧАЛО ПРОВЕРКА ЛОГИРОВАНИЯ===========
    # # line = "2026-09-03 09:19:09 | CRITICAL | Trade | critical"
    # # # 1. Вес в UTF-8 (для расчета места на диске/в логах)
    # # print(len(line.encode('utf-8')))
    # a=0
    # while a<10000:
    #     a=a+3
    #     trade_log.debug(f"debug - ======================================================================{a}")
    #     system_log.debug(f"debug - ======================================================================{a}")
    #     system_log.info(f"info - ======================================================================{a + 1}")
    #     system_log.warning(f"warning - ======================================================================{a + 2}")
    #     debug_log.info(f"warning - ======================================================================{a + 2}")

    # ==========КОНЕЦ ПРОВЕРКА ЛОГИРОВАНИЯ============




    # ===========НАЧАЛО ПОКУПКА ======================
    # for tiker, figi in tuple_buy_sell[0].items():
    #     activ_pokupka(cl=cl, tiker=tiker, figi=figi)
    # ===========КОНЕЦ ПОКУПКА =======================
