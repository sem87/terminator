from utils import *


if __name__ == "__main__":
    # НАЧАЛО------ПРОВЕРКА ОБНОВЛЕНИЯ tiker_figi.json-------
    with Client(token) as cl:
        last_modified_json(cl=cl)
    # КОНЕЦ------ПРОВЕРКА ОБНОВЛЕНИЯ tiker_figi.json-------
    while True:
        try:
            getting_started = time.time()
            with Client(token) as cl:
                # НАЧАЛО------Получение и анализ данных-------
                inform.info(f"------НАЧАЛО-------")
                # НАЧАЛО------ПРОВЕРКА ПОТОМ УДАЛИТЬ------
                cleaning_dict(buy_day=buy_day, buy_hour=buy_hour, buy_15min=buy_15min, buy_itog=buy_itog,
                              sale_day=sale_day, sale_hour=sale_hour, sale_15min=sale_15min, sale_itog=sale_itog)
                # КОНЕЦ------ПРОВЕРКА-------
                for tiker, figi in read_tiker_figi_json().items():
                    # Список день, час, 15мин
                    for time_list in [(CandleInterval.CANDLE_INTERVAL_DAY.value, 50),
                                      (CandleInterval.CANDLE_INTERVAL_HOUR, 7),
                                      (CandleInterval.CANDLE_INTERVAL_15_MIN, 1)]:
                        tuple_indicator = calculate_indicator(
                            df=candl(cl=cl, day=time_list[1], interval=time_list[0], tiker=tiker, figi=figi),
                            tiker=tiker)
                        filter_list(interval=time_list[0], tiker=tiker, figi=figi, tuple_indicator=tuple_indicator)
                # Отбор словарей на покупку
                tuple_buy_sell = select_dicts(buy_day=buy_day, buy_hour=buy_hour, buy_15min=buy_15min,
                                              sale_day=sale_day,
                                              sale_hour=sale_hour, sale_15min=sale_15min)
                # КОНЕЦ------Получение и анализ данных-------
                time.sleep(10)  # Просчитать нужен ли здесь перерыв и сколько?
                # НАЧАЛО------Покупка------
                for tiker, figi in tuple_buy_sell[0].items():
                    activ_pokupka(cl=cl, tiker=tiker, figi=figi)
                # КОНЕЦ------Покупка-------
                # НАЧАЛО------Переустановка------
                time.sleep(5)  # проверить нужна ли пауза
                resetting_stop_los(cl=cl)
                # КОНЕЦ------Переустановка------
                # НАЧАЛО------ЗАПИСЬ SQL------
                trading_information(cl=cl, days=2)
                # КОНЕЦ------ЗАПИСЬ SQL-------
                # НАЧАЛО------АНАЛИЗ ИИ------

                # КОНЕЦ------АНАЛИЗ ИИ-------
                # НАЧАЛО------АНАЛИТИКА ДАННЫХ ПОИСК АНАМАЛИЙ,УРОВНЕЙ ЦЕН------

                # КОНЕЦ------АНАЛИТИКА ДАННЫХ АНАМАЛИЙ,УРОВНЕЙ ЦЕН-------

            inform.info(f"------КОНЕЦ----Время затрачено : {int(time.time() - getting_started)} сек. ----")
        except Exception as e:
            logger.info(f"ОБЩАЯ ОШИБКА: Ex as e : {e}")
        # НАЧАЛО------ОТПРАВКА ТЕЛЕГРАММ------
        send_telegram(tupl=tuple_buy_sell)
        # КОНЕЦ------ОТПРАВКА ТЕЛЕГРАММ-------
        time.sleep(900)
