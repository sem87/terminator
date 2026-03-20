import time

from pyrogram import Client as TelegramClient
from pyrogram.enums import ParseMode
from tinkoff.invest import CandleInterval, Client

from log.logger import inform, logger
from utils import (
    activ_pokupka,
    api_iddd,
    buy_15min,
    buy_day,
    buy_hour,
    buy_itog,
    calculate_indicator,
    candl,
    cleaning_dict,
    filter_list,
    get_proxy_dict,
    last_modified_json,
    proxy_url,
    read_tiker_figi_json,
    resetting_stop_los,
    sale_15min,
    sale_day,
    sale_hour,
    sale_itog,
    select_dicts,
    send_telegram,
    telegtok,
    token,
    trading_information,
)


if __name__ == "__main__":
    # НАЧАЛО------ПРОВЕРКА ОБНОВЛЕНИЯ tiker_figi.json-------
    with Client(token) as cl:
        last_modified_json(cl=cl)
    # КОНЕЦ------ПРОВЕРКА ОБНОВЛЕНИЯ tiker_figi.json-------
    # НАЧАЛО------СОЗДАЕМ TelegramClient------
    telegram_cl = TelegramClient(
        name="SEM",
        api_id=int(api_iddd) if api_iddd else None,  # 🔧 int!
        api_hash=telegtok,
        parse_mode=ParseMode.HTML,
        proxy=get_proxy_dict(proxy_url),
    )

    # 🔌 Подключаемся ОДИН раз перед циклом
    telegram_cl.start()
    inform.info("telegram Подключено (постоянное соединение)")
    # КОНЕЦ------СОЗДАЕМ TelegramClient-------
    while True:
        try:
            getting_started = time.time()
            with Client(token) as cl:
                # НАЧАЛО------Получение и анализ данных-------
                inform.info("------НАЧАЛО-------")
                # НАЧАЛО------ПРОВЕРКА ПОТОМ УДАЛИТЬ------
                cleaning_dict(
                    buy_day=buy_day,
                    buy_hour=buy_hour,
                    buy_15min=buy_15min,
                    buy_itog=buy_itog,
                    sale_day=sale_day,
                    sale_hour=sale_hour,
                    sale_15min=sale_15min,
                    sale_itog=sale_itog,
                )
                # КОНЕЦ------ПРОВЕРКА-------
                for tiker, figi in read_tiker_figi_json().items():
                    # Список день, час, 15мин
                    # CANDLE_INTERVAL_5_MIN, CANDLE_INTERVAL_15_MIN
                    for time_list in [
                        (CandleInterval.CANDLE_INTERVAL_DAY.value, 50),
                        (CandleInterval.CANDLE_INTERVAL_HOUR, 7),
                        (CandleInterval.CANDLE_INTERVAL_5_MIN, 1),
                    ]:
                        tuple_indicator = calculate_indicator(
                            df=candl(cl=cl, day=time_list[1], interval=time_list[0], tiker=tiker, figi=figi),
                            tiker=tiker,
                        )
                        filter_list(interval=time_list[0], tiker=tiker, figi=figi, tuple_indicator=tuple_indicator)
                # Отбор словарей на покупку
                tuple_buy_sell = select_dicts(
                    buy_day=buy_day,
                    buy_hour=buy_hour,
                    buy_15min=buy_15min,
                    sale_day=sale_day,
                    sale_hour=sale_hour,
                    sale_15min=sale_15min,
                )
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
        try:
            send_telegram(tupl=tuple_buy_sell, telegram_cl=telegram_cl)
        except KeyboardInterrupt as e:
            logger.info(f"Прервано пользователем отправка телеграм Ex as e : {e}")
        # КОНЕЦ------ОТПРАВКА ТЕЛЕГРАММ-------
        time.sleep(530)
