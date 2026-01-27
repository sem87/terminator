import os
from dotenv import load_dotenv
from tinkoff.invest import (CandleInterval, Client, InstrumentIdType,
                            OperationState, OperationType, OrderDirection,
                            OrderType, Quotation, RequestError, OrderState)
from tinkoff.invest.services import (InstrumentsService, MarketDataService, StopOrderDirection, StopOrderExpirationType,
                                     StopOrderType)
from tinkoff.invest.utils import now, quotation_to_decimal, decimal_to_quotation
from tinkoff.invest import InstrumentStatus
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import json
from log.logger import *
from sql_terminator import *
import time
from datetime import UTC, datetime, timedelta, date
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands

from pyrogram import Client as TelegramClient
from pyrogram.enums import ParseMode

"""ДЛЯ ЧТЕНИЯ ТОКЕНА"""
load_dotenv("../terminator/.env.term")  # Если файл в той же папке, что и скрипт
token = os.getenv("TOKSell")  # Обратите внимание на имя переменной
accid = os.getenv("aOcid")  # Обратите внимание на имя переменной
telegtok = os.getenv("telegtokeng")
groupt = os.getenv("groupt")
api_iddd = os.getenv("api_iddd")

# -----------СЛОВАРИ---------
buy_day = {}
buy_hour = {}
buy_15min = {}
buy_itog = {}
sale_day = {}
sale_hour = {}
sale_15min = {}
sale_itog = {}

# -----------ТИКЕРЫ ДЛЯ РАБОТЫ---------
tiker_figi = {}


# Полный список
# tikers = [
#     "SBER", "ROSN", "LKOH", "ZAYM", "SNGS", "TATN", "BANE", "ELFV", "SLAV", "YAKG", "RNFT", "SIBN", "TGKN", "NVTK",
#     "GAZP", "MOEX", "MBNK", "BSPB", "SPBE", "ZAYM", "RENI", "VTBR", "SVCB", "CBOM", "MGKL", "CARM", "MGNT", "GCHE",
#     "KROT", "LENT", "SVAV", "AQUA", "HNFG", "BELU", "ABRD", "OKEY", "NKHP", "GTRK", "WUSH", "MSTT", "EUTR", "KMAZ",
#     "FLOT", "FESH", "UWGN", "NMTP", "ABIO", "HEAD", "ASTR", "DELI", "LEAS", "KZIZ", "SMLT", "LSRG", "PIKK", "TGKJ",
#     "VSMO", "PLZL", "AKRN", "LNZL", "CHMK", "PHOR", "CHMF", "KAZT", "ENPG", "NLMK", "GMKN", "NKNC", "KZOS", "MRKZ",
#     "ALRS", "RUAL", "PRFN", "UGLD", "NSVZ", "RTKM", "CNTL", "TTLK", "VRSB", "PMSB", "KLSB", "LSNG", "IRAO", "DVEC",
#     "UPRO", "MSRS", "MRKC", "MRKP", "MRKV", "MRKY", "T"]
# Чем торгую
# tikers = ["SBER", "ROSN", "SNGS", "TATN", "RNFT", "SIBN", "NVTK", "GAZP", "VTBR", "EUTR", "FLOT", "HEAD",
#           "ASTR", "SMLT", "LSRG", "PIKK", "ALRS", "RUAL", "PLZL", "SELG", "GMKN"]


# -------------------РАБОТА С JSON И ПОДГОТОВКА СЛОВАРЕЙ-------------
def read_tiker_figi_json() -> dict:
    """ЧИТАЕТ ДАННЫЕ ИЗ tiker_figi_json"""
    try:
        with open("tiker_figi.json", "r", encoding="utf-8") as tiker_figi:
            dict_tiker_figi = json.load(tiker_figi)  # Загружает весь JSON как словарь
        return dict_tiker_figi
    except json.JSONDecodeError as e:
        logger.info(f"Файл tiker_figi.json повреждён (некорректный JSON): {e}")
        return {}
    except (OSError, IOError) as e:
        logger.info(f"Ошибка чтения файла tiker_figi.json: {e}")
        return {}
    except Exception as e:
        logger.info(f"read_tiker_figi_json неизвестная ошибка json, Exception as e : {e}")
        return {}


# def read_time_dict_json() -> dict:
#     """ЧИТАЕТ ДАННЫЕ ИЗ time_dict_json"""
#     try:
#         with open("time_dict.json", "r", encoding="utf-8") as time_dict:
#             dict_time_dict = json.load(time_dict)  # Загружает весь JSON как словарь
#         return dict_time_dict
#     except json.JSONDecodeError as e:
#         logger.info(f"Файл time_dict.json повреждён (некорректный JSON): {e}")
#         return {}
#     except (OSError, IOError) as e:
#         logger.info(f"Ошибка чтения файла time_dict.json: {e}")
#         return {}
#     except Exception as e:
#         logger.info(f"time_dict.json неизвестная ошибка json, Exception as e : {e}")
#         return {}
#
#
# class DataAnalysis:
#     """СОБИРАЕТ,ОБРАБАТЫВАЕТ ДАННЫЕ ПО АКЦИЯМ, СОРТИРУЕТ НА ПОКУПКУ ПРОДАЖУ"""
#     pass


def cleaning_dict(buy_day: dict, buy_hour: dict, buy_15min: dict, buy_itog: dict, sale_day: dict, sale_hour: dict,
                  sale_15min: dict, sale_itog: dict):
    """ОЧИЩАЕТ СЛОВАРИ"""
    try:
        buy_day.clear()
        buy_hour.clear()
        buy_15min.clear()
        buy_itog.clear()
        sale_day.clear()
        sale_hour.clear()
        sale_15min.clear()
        sale_itog.clear()
    except Exception as e:
        logger.info(f"cleaning_dict() ошибка очистка словарей : Exception as e : {e}")


def get_figi(cl, tiker: str):
    """ИЗВЛЕКАЕТ ИЗ ТИКЕРА ФИГИ"""
    try:
        instruments: InstrumentsService = cl.instruments
        # market_data: MarketDataService = cl.market_data
        # Забирает данные для INSTRUMENT_STATUS_BASE
        df = pd.DataFrame(instruments.shares(
            instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments,
                          columns=["name", "figi", "ticker", "class_code"])
        # for method in ['shares' АКЦИИ, 'bonds', 'etfs' ]:
        # 'currencies', 'futures']:  ОБЛИГАЦИИ ЕТФ ОПЦИОНЫ НУЖНО РАЗБИРАТЬСЯ
        figi = df[df["ticker"] == tiker]["figi"].iloc[0]
        return figi
    except Exception as e:
        logger.info(f" {tiker} - функция get_figi() - не получается достать figi Exception as e : {e}")
        return None


def list_active_tickers():
    """ПОЛУЧАЕМ СПИСОК ВСЕ АКЦИИ 'на рынке' ИЗ БАЗЫ"""
    try:
        active_tickers = session.query(AnalysisTiker.tiker).filter(AnalysisTiker.activity == "на рынке").all()
        active_tickers = [row[0] for row in active_tickers]
        # print(f"СПИСОК АКТИВНЫХ АКЦИЙ {active_tickers}")
        return active_tickers
    except Exception as e:
        logger.info(f"list_active_tickers() - не получается достать ВСЕ АКЦИИ 'на рынке' ИЗ БАЗЫ Exception as e : {e}")


def save_all_json(cl):
    """СОХРАНЯЕТ В JSON "tiker":"figi" """
    try:
        tikers = list_active_tickers()
        for tiker in tikers:
            tiker_figi[tiker] = get_figi(tiker=tiker, cl=cl)
        with open("tiker_figi.json", "w", encoding="utf-8") as f:
            json.dump(tiker_figi, f, indent=4, ensure_ascii=False, sort_keys=True)
        return None
    except Exception as e:
        logger.info(f" - функция save_all_json - не получается сохранить JSON.Exception as e : {e}")
        return None


def last_modified_json(cl):
    """ПРОВЕРЯЕТ ДАВНО ЛИ ОБНОВЛЯЛСЯ tiker_figi.json"""
    try:
        # Получаем время последнего изменения файла (в секундах с эпохи)
        if os.path.exists("tiker_figi.json"):
            last_modified = os.path.getmtime("tiker_figi.json")
            # Разница во времени
            delta = datetime.now() - datetime.fromtimestamp(last_modified)
            if delta >= timedelta(days=7):
                inform.info(f"Обновляем ФИГИ в tiker_figi.json. Прошло {delta.days} дней!!!")
                save_all_json(cl=cl)
            else:
                inform.info(f"Файл был изменён менее 7 дней. Прошло только {delta.days} дней!!! ВСЕ ОК.")
    except Exception as e:
        logger.info(f"last_modified_json() - (ошибка) нет файла tiker_figi.json: Exception as e : {e}")


# -------------------ФУНКЦИИ ДЛЯ ОБРАБОТКИ ДАННЫХ-------------
def candl(cl, day: int, interval, figi: str, tiker: str) -> pd.DataFrame:
    """ИЗВЛЕКАЕТ ДАННЫЕ ИЗ СВЕЧЕК ЗА ОПРЕДЕЛЕННЫЙ ПЕРИОД"""
    try:
        # Получаем данные о свечах указываем интервал
        candle_data = cl.market_data.get_candles(
            figi=figi,
            from_=now() - timedelta(days=day),  # было day=1 (неверно)
            to=now(),  # было datetime.UTC() (неверно)
            interval=interval)  # '''CandleInterval.CANDLE_INTERVAL_15_MIN  # нужно указать конкретный интервал'''
        # Преобразуем в удобный формат
        candles = []
        for candle in candle_data.candles:
            candles.append({"Время": candle.time.strftime("%Y-%m-%d %H:%M:%S"),
                            "Открытие": candle.open.units + candle.open.nano / 1e9,
                            "МАХ": candle.high.units + candle.high.nano / 1e9,
                            "MIN": candle.low.units + candle.low.nano / 1e9,
                            "Закрытие": candle.close.units + candle.close.nano / 1e9,
                            "Объем": candle.volume})
        # Создаем DataFrame для красивого отображения
        df = pd.DataFrame(candles)
        return df
    except Exception as e:
        logger.info(f"{tiker} - candl() извлечение данных : {interval},период : {day} , Exception as e : {e}")
        df = pd.DataFrame(None)
        # Проверить когда пустой Дата фрейм???
        return df


def calculate_indicator(df: pd.DataFrame, tiker: str) -> tuple:
    """Рассчитывает технические индикаторы для DataFrame"""
    """СМЫСЛ В ТОМ ЧТОБЫ УСТАНОВИТЬ ВОСХОДЯЩИЙ ЛИ ТРЕНД"""
    try:
        # Преобразуем время в datetime и устанавливаем как индекс
        df["Время"] = pd.to_datetime(df["Время"])
        df.set_index("Время", inplace=True)
        "SMA 10"
        # Рассчитываем SMA с периодом 10 предел в 45 почему-то
        sma_indicator = SMAIndicator(close=df["Закрытие"], window=10)
        df["SMA_10"] = sma_indicator.sma_indicator()
        # Получаем последние значения
        last_sma_10_1 = df["SMA_10"].iloc[-1]
        last_sma_10_2 = df["SMA_10"].iloc[-2]
        last_sma_10_3 = df["SMA_10"].iloc[-3]
        last_sma_10_4 = df["SMA_10"].iloc[-4]
        "КОНЕЦ SMA 10"
        """НАЧАЛО RSI"""
        # Рассчитываем RSI (период 14 по умолчанию)
        rsi_indicator = RSIIndicator(close=df["Закрытие"], window=14)
        df["RSI"] = rsi_indicator.rsi()
        last_rsi = df["RSI"].iloc[-1]  # Последнее значение
        prev_rsi = df["RSI"].iloc[-2]  # Предпоследнее значение
        prev_rsi_3 = df["RSI"].iloc[-3]
        prev_rsi_4 = df["RSI"].iloc[-4]
        """КОНЕЦ RSI"""
        """НАЧАЛО MACD"""
        # Рассчитываем MACD
        macd_indicator = MACD(close=df["Закрытие"], window_slow=26, window_fast=12, window_sign=9)
        df["MACD"] = macd_indicator.macd()  # Линия MACD (разница 12 и 26 EMA)
        df["MACD_Signal"] = macd_indicator.macd_signal()  # Сигнальная линия (EMA от MACD)
        df["MACD_Hist"] = macd_indicator.macd_diff()  # Гистограмма (MACD - Signal)
        last_MACD = df["MACD_Hist"].iloc[-1]
        prev_MACD = df["MACD_Hist"].iloc[-2]
        prev_MACD_3 = df["MACD_Hist"].iloc[-3]
        prev_MACD_4 = df["MACD_Hist"].iloc[-4]
        """КОНЕЦ MACD"""
        """НАЧАЛО Bollinger"""
        # Инициализация индикатора Bollinger Bands
        indicator_bb = BollingerBands(close=df["Закрытие"], window=20, window_dev=2)
        # Добавление полос Боллинджера в DataFrame
        # df['bb_upper'] = indicator_bb.bollinger_hband()  # Верхняя полоса
        df["bb_middle"] = indicator_bb.bollinger_mavg()  # Средняя линия (SMA)
        # df['bb_lower'] = indicator_bb.bollinger_lband()  # Нижняя полоса
        midle_Bollinger = df["bb_middle"].iloc[-1]  # Средняя линия Боллинджера
        """КОНЕЦ Bollinger"""
        close = df["Закрытие"].iloc[-1]  # Цена закрытия
        """ДОСТАЕМ ОБЪЕМ"""
        volume = df["Объем"].iloc[-1]  # Объем последний
        mean_volume = df["Объем"].iloc[-10:].mean()
        """КОНЕЦ ОБЪЕМ"""
        return (last_rsi, prev_rsi, prev_rsi_3, prev_rsi_4, last_MACD, prev_MACD, prev_MACD_3,
                prev_MACD_4, last_sma_10_1, last_sma_10_2, last_sma_10_3, last_sma_10_4, close, midle_Bollinger,
                volume, mean_volume)  # Возвращаем последние и предпоследние значения
    except Exception as e:
        logger.info(f"{tiker} - calculate_indicator() расчет тех индикатора : Exception as e : {e}")
        return ()


def filter_list(interval, figi: str, tiker: str, tuple_indicator: tuple):
    """ФИЛЬТР ПО СПИСКАМ НА ПОКУПКУ И ПРОДАЖУ"""
    try:
        if interval == CandleInterval.CANDLE_INTERVAL_DAY:
            """ДНЕВНОЙ ИНТЕРВАЛ УСЛОВИЕ"""
            timeframe = "day"
            # ПОКУПКА
            # 1_buy_day) ищем ДНО MACD.RSI 50 -_-'   МАКСИМАЛЬНО УЖЕСТОЧИТЬ
            # (prev_MACD_3 < prev_MACD_4< 0) and (prev_MACD_3<prev_MACD<last_MACD) and (prev_rsi_3<last_rsi<50)
            if ((tuple_indicator[6] < tuple_indicator[7] < 0) and (
                    tuple_indicator[6] < tuple_indicator[5] < tuple_indicator[4] < 0)) and (
                    tuple_indicator[2] < tuple_indicator[0] < 50):
                """ДНО ДЕНЬ MACD.RSI"""
                buy_day[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="buy",
                                                strategy="1_buy_day) ищем ДНО MACD.RSI 50 -_-'",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # 2_buy_day) возраст SMA 10.RSI<65 _-'   МАКСИМАЛЬНО УЖЕСТОЧИТЬ
            # (last_sma_10_3 < last_sma_10_2 < last_sma_10_1) and (prev_rsi_3 < last_rsi < 65)
            elif (tuple_indicator[10] < tuple_indicator[9] < tuple_indicator[8]) and (
                    tuple_indicator[2] < tuple_indicator[0] < 65):
                """ВОЗРОСТАНИЕ SMA 10"""
                buy_day[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="buy",
                                                strategy="2_buy_day) возраст SMA 10.RSI<65 _-'",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # ПРОДАЖА
            # 1_sell_day) ищем ВЕРХ MACD.RSI 50 -'-_   МАКСИМАЛЬНО УЖЕСТОЧИТЬ
            # (prev_MACD_4 < prev_MACD_3) and (last_MACD<prev_MACD<prev_MACD_3) and (50<last_rsi<prev_rsi_3)
            elif (tuple_indicator[7] < tuple_indicator[6]) and (
                    tuple_indicator[4] < tuple_indicator[5] < tuple_indicator[6]) and (
                    50 < tuple_indicator[0] < tuple_indicator[2]):
                """ВЕРХ MACD.RSI"""
                sale_day[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="sell",
                                                strategy="1_sell_day) ищем ВЕРХ MACD.RSI 50 -'-_ ",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # 2_sell_day) убывающий SMA 10.RSI>45 '-_   МАКСИМАЛЬНО УЖЕСТОЧИТЬ
            # (last_sma_10_1  < last_sma_10_2 < last_sma_10_3) and (50<last_rsi<prev_rsi_3)
            elif (tuple_indicator[8] < tuple_indicator[9] < tuple_indicator[10]) and (
                    45 < tuple_indicator[0] < tuple_indicator[2]):
                """УБЫВАЮЩИЙ SMA 10.RSI>45 '-_"""
                sale_day[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="sell",
                                                strategy="2_sell_day) убывающий SMA 10.RSI>45 '-_ ",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            else:
                """НИ КУДА НЕ ПОПАЛО"""
                pass
        elif interval == CandleInterval.CANDLE_INTERVAL_HOUR:
            """ЧАСОВОЙ ИНТЕРВАЛ УСЛОВИЕ"""
            timeframe = "hour"
            # ПОКУПКА
            # 1_buy_hour) возраст SMA10 RSI < 65 .-'
            # (last_sma_10_4<last_sma_10_2<last_sma_10_1) and (prev_rsi_3<last_rsi<65)
            if (tuple_indicator[11] < tuple_indicator[9] < tuple_indicator[8]) and (
                    tuple_indicator[2] < tuple_indicator[0] < 65):
                "SMA 10 ВОЗРАСТАЕТ "
                buy_hour[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="buy",
                                                strategy="1_buy_hour) возраст SMA10 .-'",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # ПРОДАЖА
            # 1_sell_hour) убывающий SMA10 и RSI > 45 '-.
            # (last_sma_10_1<last_sma_10_2<last_sma_10_4) and (45<last_rsi<prev_rsi_3)
            elif (tuple_indicator[8] < tuple_indicator[9] < tuple_indicator[11]) and (
                    45 < tuple_indicator[0] < tuple_indicator[2]):
                "SMA 10 УБЫВАЕТ"
                sale_hour[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="sell",
                                                strategy="1_sell_hour) убывающий SMA10 и RSI > 45 '-.",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            else:
                """НИ КУДА НЕ ПОПАЛО"""
                pass
        elif interval == CandleInterval.CANDLE_INTERVAL_15_MIN:
            """15 МИНУТНЫЙ ИНТЕРВАЛ УСЛОВИЕ"""
            timeframe = "15_min"
            # ПОКУПКА
            # 1_buy_15_min) нижняя т MACD. -_-'
            # (цена закрытия < средняя боллинджера) and (prev_MACD_3 < prev_MACD_4) and
            # (prev_MACD_3<prev_MACD<last_MACD<0) and (prev_rsi_3<last_rsi<45)
            if ((tuple_indicator[12] < tuple_indicator[13]) and (tuple_indicator[6] < tuple_indicator[7]) and (
                    tuple_indicator[6] < tuple_indicator[5] < tuple_indicator[4] < 0) and (
                    tuple_indicator[2] < tuple_indicator[0] < 45)):
                "ОТБИРАЕМ В САМОМ НИЗУ 15 МИН"
                buy_15min[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="buy",
                                                strategy="1_buy_15_min) нижняя т MACD. -_-'",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # 2_buy_15_min) возраст MACD. _-'
            # (цена закрытия < средняя боллинджера) and
            # (prev_MACD_3<prev_MACD<last_MACD<0) and (prev_rsi_3<last_rsi<45)
            elif ((tuple_indicator[12] < tuple_indicator[13]) and (
                    tuple_indicator[6] < tuple_indicator[5] < tuple_indicator[4] < 0) and (
                          tuple_indicator[2] < tuple_indicator[0] < 45)):
                "ОТБИРАЕМ В САМОМ НИЗУ 15 МИН ПОСЛЕДУЮШИЕ СВЕЧИ MACD УВЕЛИЧИВАЮТСЯ НО <0"
                buy_15min[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="buy",
                                                strategy="2_buy_15_min) возраст MACD. _-'",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # 3_buy_15_min) возраст SMA10 но боллинжер огранич"   (но похоже это редкие случаи)
            # (цена закрытия < средняя боллинджера) and
            # (last_sma_10_3<last_sma_10_2<last_sma_10_1) and (prev_rsi_3<last_rsi<50)
            elif ((tuple_indicator[12] < tuple_indicator[13]) and (
                    tuple_indicator[10] < tuple_indicator[9] < tuple_indicator[8]) and (
                          tuple_indicator[2] < tuple_indicator[0] < 50)):
                "SMA 10 ВОЗРАСТАЕТ НО БОЛЛИНДЖЕР ОГРАНИЧИВАЕТ"
                buy_15min[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="buy",
                                                strategy="3_buy_15_min) возраст SMA10 но боллинжер огранич",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # 4_buy_15_min) возраст SMA10 и rsi < 50. (ЕСЛИ УВЕЛИЧИВАТЬ ЭТО ЧИСЛО ТО МОЖЕТ МНОГО НЕУДАЧ!!)
            # (last_sma_10_3<last_sma_10_2<last_sma_10_1) and (prev_rsi_3<last_rsi<50)
            elif (tuple_indicator[10] < tuple_indicator[9] < tuple_indicator[8]) and (
                    tuple_indicator[2] < tuple_indicator[0] < 50):
                "SMA 10 ВОЗРАСТАЕТ"
                buy_15min[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="buy",
                                                strategy="4_buy_15_min) возраст SMA10 и rsi < 50.",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # ПРОДАЖА
            # 1_sell_15_min) верхняя т. MACD. -'-_
            # (средняя боллинджера < цена закрытия) and (prev_MACD_4 < prev_MACD_3) and
            # (0<last_MACD<prev_MACD<prev_MACD_3) and (55<last_rsi<prev_rsi_3)
            elif ((tuple_indicator[13] < tuple_indicator[12]) and (tuple_indicator[7] < tuple_indicator[6]) and (
                    0 < tuple_indicator[4] < tuple_indicator[5] < tuple_indicator[6]) and (
                          55 < tuple_indicator[0] < tuple_indicator[2])):
                "ОТБИРАЕМ В САМОМ ВЕРХУ 15 МИН"
                sale_15min[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="sell",
                                                strategy="1_sell_15_min) верхняя т. MACD. -'-_",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # 2_sell_15_min) убывающий MACD '-_
            # (средняя боллинджера < цена закрытия) and
            # (0<last_MACD<prev_MACD<prev_MACD_3) and (55<last_rsi<prev_rsi_3)
            elif ((tuple_indicator[13] < tuple_indicator[12]) and (
                    0 < tuple_indicator[4] < tuple_indicator[5] < tuple_indicator[6]) and (
                          55 < tuple_indicator[0] < tuple_indicator[2])):
                "ОТБИРАЕМ В САМОМ ВЕРХУ 15 МИН ПОСЛЕДУЮШИЕ СВЕЧИ MACD МОЖЕТ < 0"
                sale_15min[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="sell",
                                                strategy="2_sell_15_min) убывающий MACD '-_",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # 3_sell_15_min) убывающий SMA10 но боллинжер ограничивает."   (но похоже это редкие случаи)
            # (средняя боллинджера < цена закрытия) and
            # (last_sma_10_1<last_sma_10_2<last_sma_10_3) and (60<last_rsi<prev_rsi_3)
            elif ((tuple_indicator[13] < tuple_indicator[12]) and (
                    tuple_indicator[8] < tuple_indicator[9] < tuple_indicator[10]) and (
                          60 < tuple_indicator[0] < tuple_indicator[2])):
                "SMA 10 УБЫВАЕТ НО БОЛЛИНДЖЕР ОГРАНИЧИВАЕТ"
                sale_15min[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="sell",
                                                strategy="3_sell_15_min) убывающий SMA10 но боллинжер ограничивает.",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            # 4_sell_15_min) убывающий SMA10 и rsi > 60 (ЕСЛИ уменьшать ЭТО ЧИСЛО ТО МОЖЕТ МНОГО НЕУДАЧ!!!!)
            # (last_sma_10_1<last_sma_10_2<last_sma_10_3) and (60<last_rsi<prev_rsi_3)
            elif (tuple_indicator[8] < tuple_indicator[9] < tuple_indicator[10]) and (
                    60 < tuple_indicator[0] < tuple_indicator[2]):
                "SMA 10 УБЫВАЕТ"
                sale_15min[tiker] = figi
                filter_tiker = FilterTickerDict(tiker=tiker, timeframe=timeframe, action="sell",
                                                strategy="4_sell_15_min) убывающий SMA10 и rsi > 60",
                                                description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}")
                session.add(filter_tiker)
                session.commit()
            else:
                """НИ КУДА НЕ ПОПАЛО"""
                pass
        else:
            logger.info(f"{tiker} - filter_list() - НЕТ НУЖНОГО ИНТЕРВАЛА")
    except Exception as e:
        logger.info(f"{tiker} - filter_list() ошибка записи в список : Exception as e : {e}")


def select_dicts(buy_day: dict, buy_hour: dict, buy_15min: dict, sale_day: dict, sale_hour: dict,
                 sale_15min: dict):
    """ОТБОР СЛОВАРЕЙ НА ПОКУПКУ"""
    try:
        # На покупку
        buy_itog_2 = {tiker: figi for tiker, figi in buy_day.items() if tiker in buy_15min}
        buy_itog_3 = {tiker: figi for tiker, figi in buy_hour.items() if tiker in buy_15min}
        buy_itog = {**buy_itog_2, **buy_itog_3}
        # На продажу
        sale_itog_2 = {tiker: figi for tiker, figi in sale_day.items() if tiker in sale_15min}
        sale_itog_3 = {tiker: figi for tiker, figi in sale_hour.items() if tiker in sale_15min}
        sale_itog = {**sale_itog_2, **sale_itog_3}
        inform.info(f"Buy день- {buy_day.keys()}")
        inform.info(f"Buy час- {buy_hour.keys()}")
        inform.info(f"Buy 15мин- {buy_15min.keys()}")
        inform.info(f"Buy ИТОГО- {buy_itog.keys()}")
        inform.info(f"Sale день- {sale_day.keys()}")
        inform.info(f"Sale час- {sale_hour.keys()}")
        inform.info(f"Sale 15мин- {sale_15min.keys()}")
        inform.info(f"Sale ИТОГО- {sale_itog.keys()}")
        # Возвращает кортеж словарей
        return buy_itog, sale_itog  # Автоматически возвращает кортеж из 2х словарей
    except Exception as e:
        logger.info(f"select_dicts() ошибка отбора в buy_itog, sale_itog : Exception as e : {e}")


# -------ФУНКЦИИ ПОКУПКИ ПРОДАЖИ ПЕРЕУСТАНОВКИ--------
def already_exist(cl) -> dict:
    """ПОЛУЧАЕМ СЛОВАРЬ АКТИВНЫХ ЗАЯВОК"""
    try:
        dict_already_exist = {}
        activ_orders = cl.operations.get_portfolio(account_id=accid).positions
        for activ_order in activ_orders:
            dict_already_exist[activ_order.ticker] = activ_order.figi
        return dict_already_exist
    except Exception as e:
        logger.info(f"already_exist() ошибка в получении активных заявок : Exception as e : {e}")


def calculation_number_lots(cl, figi: str, tiker: str):
    """РАСЧЕТ КОЛИЧЕСТВА ЛОТОВ НА СУММУ 5000"""
    try:
        # Получаем текущую цену инструмента (последняя сделка)
        last_price = cl.market_data.get_last_prices(figi=[figi]).last_prices[0]
        current_price = float(quotation_to_decimal(last_price.price))
        # Получаем информацию о лоте
        instrument = cl.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                                                      id=figi).instrument
        lot_size = int(instrument.lot)  # Количество единиц в лоте
        positions = cl.operations.get_positions(account_id=accid)
        # print('ОЛИЧЕСТВО ДЕНЕГ НА СЧЕТЕ   '+str(positions))
        # Выводим доступные деньги на счете
        for money in positions.money:
            units = money.units
            # Условие чтобы не больше 5000 на 1 позицию
            """ПЕРЕДЕЛАЙ УСЛОВИЕ НА 4900"""
            if units > 3900:
                quantity = int(3900 / (current_price * lot_size))
                return quantity
            else:
                quantity = int(units / (current_price * lot_size))
                return quantity
            # Сколько лотов можно купить
    except Exception as e:
        logger.info(f"{tiker} - calculation_number_lots() ошибка расчета количества лотов : Exception as e : {e}")


def opredelaem_schag(cl, figi: str, tiker: str) -> Decimal:
    """ДЛЯ ОПРЕДЕЛЕНИЯ ШАГА ЦЕНЫ АКТИВА"""
    try:
        instruments: InstrumentsService = cl.instruments
        # Для акций
        instrument = instruments.share_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi
        ).instrument
        min_price_increment = instrument.min_price_increment.nano / 1000000000
        return Decimal(min_price_increment)
    except Exception as e:
        logger.info(f"{tiker} - opredelaem_schag() ошибка определения шага цены актива : Exception as e : {e}")


def activ_pokupka(cl, figi: str, tiker: str):
    """ПОКУПКА АКТИВА, РАССТОНОВКА СТОП-ЛОСА И ТЕЙК-ПРОФИТА"""
    try:
        # УСЛОВИЯ
        if tiker in already_exist(cl=cl):
            """ПРОВЕРКА КУПЛЕН УЖЕ АКТИВ ИЛИ НЕТ"""
            print(f"{tiker} - УЖЕ КУПЛЕНО")
            inform.info(f"{tiker} - УЖЕ КУПЛЕНО")
        else:
            """ПОКУПАЕМ ПО ЛУЧШЕЙ ЦЕНЕ КОТОРАЯ ЕСТЬ НА РЫНКЕ"""
            # Расчет кол-ва лотов
            quantity = calculation_number_lots(cl=cl, figi=figi, tiker=tiker)
            if quantity <= 0:
                inform.info(f"НЕ КУПИЛИ - {tiker} . т.к. можно купить {quantity} шт")
                """НАЧАЛО САМОЙ ПОКУПКИ"""
            else:
                try:
                    # Покупаем
                    cl.orders.post_order(order_id="", figi=figi, quantity=quantity, account_id=accid,
                                         direction=OrderDirection.ORDER_DIRECTION_BUY,  # на продажу SELL
                                         order_type=OrderType.ORDER_TYPE_MARKET)
                    inform.info(f"КУПИЛ - {tiker} . В КОЛИЧЕСТВЕ {quantity}")
                except RequestError as e:
                    logger.info(f"{tiker} - activ_pokupka() RequestError : {e}")
                    # Специальная обработка для ошибки 30015
                    if e.details == 30015:
                        logger.info(f"{tiker}-Некорректное количество лотов: {quantity} шт. Ошибка 30015")
                except Exception as e:
                    logger.info(f"{tiker} - activ_pokupka() ошибка в выставлении пост ордера: Exception as e : {e}")
                """КОНЕЦ САМОЙ ПОКУПКИ"""
                time.sleep(25)  # Нужно чтобы прогрузилась покупка. ВЫЯСНИТЬ МИНИМУМ ПРОГРУЗКИ
                """ИНФОРМАЦИЯ О ПОЗИЦИИ НА СЧЕТЕ.ЗА СКОЛЬКО КУПИЛИ И ЛОТНОСТЬ"""
                # Получаем информацию о позициях на счёте
                positions = cl.operations.get_portfolio(account_id=accid).positions
                # Ищем нужный инструмент по FIGI
                for position in positions:
                    if position.figi == figi:
                        average_price = position.average_position_price  # Средняя цена покупки (MoneyValue)
                        quantity_lots = position.quantity_lots  # Количество лотов (Decimal)
                        # Конвертируем MoneyValue в Decimal
                        price_rub = Decimal(average_price.units + average_price.nano / 1e9)
                        quantity_lots_new = int(quantity_lots.units + quantity_lots.nano / 1e9)  # переделать
                        """КОНЕЦ ИНФОРМАЦИИ О ПОЗИЦИИ НА СЧЕТЕ.ЗА СКОЛЬКО КУПИЛИ И ЛОТНОСТЬ"""
                        time.sleep(2)
                        schag = opredelaem_schag(cl=cl, figi=figi, tiker=tiker)
                        """НАЧАЛО ТЕЙК-ПРОФИТ ЗАЯВКИ"""  # продажа при достижении take_profit_price
                        coeff_take_profit_price = Decimal(1.05)
                        cl.stop_orders.post_stop_order(
                            figi=figi,
                            quantity=quantity_lots_new,  # Количество лотов
                            price=decimal_to_quotation(
                                ((price_rub * coeff_take_profit_price) / schag).quantize(Decimal('1'),
                                                                                         rounding=ROUND_HALF_UP) * schag),
                            stop_price=decimal_to_quotation(
                                ((price_rub * coeff_take_profit_price) / schag).quantize(Decimal('1'),
                                                                                         rounding=ROUND_HALF_UP) * schag),
                            # Стоп-цена заявки за 1 инструмент
                            direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                            account_id=accid,
                            expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
                            stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT,
                        )  # STOP_ORDER_TYPE_STOP_LIMIT    ИЛИ  STOP_ORDER_TYPE_STOP_LOSS
                        # instrument_id = StopOrdersService
                        inform.info(
                            f"ТЕЙК-ПРОФИТ-{tiker}->ЦЕН{round((price_rub * coeff_take_profit_price / schag) * schag, 3)}"
                            f" В КОЛИЧЕСТВЕ {quantity_lots_new}")
                        """КОНЕЦ ТЕЙК-ПРОФИТ ЗАЯВКИ"""
                        """НАЧАЛО СТОП-ЛОСС ЗАЯВКИ"""
                        # Стоп-лимит заявка (продажа при достижении take_profit_price)
                        coeff_stop_loss_price = Decimal(0.9962)  # ВОЗМОЖНО ЕЩЕ УТОЧНИТЬ ЭТУ ЦИФРУ
                        cl.stop_orders.post_stop_order(
                            figi=figi,
                            quantity=quantity_lots_new,  # Количество лотов
                            price=decimal_to_quotation(
                                ((price_rub * coeff_stop_loss_price) / schag).quantize(Decimal('1'),
                                                                                       rounding=ROUND_HALF_UP) * schag),
                            stop_price=decimal_to_quotation(
                                ((price_rub * coeff_stop_loss_price) / schag).quantize(Decimal('1'),
                                                                                       rounding=ROUND_HALF_UP) * schag),
                            # Стоп-цена заявки за 1 инструмент/
                            direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                            account_id=accid,
                            expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
                            stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS,
                        )  # STOP_ORDER_TYPE_STOP_LIMIT    ИЛИ  STOP_ORDER_TYPE_STOP_LOSS
                        inform.info(
                            f"СТОП-ЛИМИТ-{tiker}->ЦЕНА {round((price_rub * coeff_stop_loss_price / schag) * schag, 3)}"
                            f" В КОЛИЧЕСТВЕ {quantity_lots_new}")
                        """КОНЕЦ СТОП-ЛОСС ЗАЯВКИ"""
                """КОНЕЦ РАСЧИТАЕМ И ВЫСТАВИМ СТОП-ЛОСС И ТЕЙК-ПРОФИТ"""
    except Exception as e:
        logger.info(f"{tiker} - activ_pokupka() ошибка при покупки актива : Exception as e : {e}")


def price_active_stop_loss(cl, figi: str, tiker: str):  # -> Decimal
    """ПОЛУЧАЕМ ЦЕНУ ИСПОЛНЕНИЯ АКТИВНОЙ СТОП-ЗАЯВКИ"""
    try:
        # Получаем все стоп-заявки
        inform_stops = cl.stop_orders.get_stop_orders(account_id=accid).stop_orders
        # Находим нужную стоп-заявку
        stop_order_info = None
        for inform_stop in inform_stops:
            if (inform_stop.direction == StopOrderDirection.STOP_ORDER_DIRECTION_SELL
                    and inform_stop.order_type == StopOrderType.STOP_ORDER_TYPE_STOP_LOSS
                    and inform_stop.figi == figi):
                stop_order_info = inform_stop
                break
        if stop_order_info:
            # Получаем цену исполнения
            stop_price = quotation_to_decimal(stop_order_info.stop_price)  # обратить внимание quotation_to_decimal
            return stop_price
    except Exception as e:
        logger.info(f"{tiker} - price_active_stop_loss() ошибка получения цены СТОП-ЛОСА : Exception as e : {e}")


def moving_stop_los(cl, figi, tiker, quantity: int, price_rub: Decimal, coeff_sl_price: Decimal, schag: Decimal):
    """ИНФОРМАЦИЯ, ОТМЕНА АКТИВНЫХ СТОП-ЗАЯВОК И ПЕРЕДВИГАНИЕ СТОП-ЛОСА"""
    try:
        inform_stops = cl.stop_orders.get_stop_orders(account_id=accid).stop_orders
        # Находим нужную стоп-заявку
        stop_order_to_cancel = None
        for inform_stop in inform_stops:
            if (
                    inform_stop.direction == StopOrderDirection.STOP_ORDER_DIRECTION_SELL
                    and inform_stop.order_type == StopOrderType.STOP_ORDER_TYPE_STOP_LOSS
                    and inform_stop.figi == figi):
                stop_order_to_cancel = inform_stop.stop_order_id
                # Если нашли заявку, отменяем её
                if stop_order_to_cancel:
                    cl.stop_orders.cancel_stop_order(account_id=accid, stop_order_id=stop_order_to_cancel)
        # time.sleep(10)  # Проверить необходимость
        """УСТАНАВЛИВАЕМ НОВЫЙ СТОП-ЛОСС"""
        # Стоп-лимит заявка (продажа при достижении take_profit_price)
        cl.stop_orders.post_stop_order(
            figi=figi,
            quantity=quantity,  # Количество лотов
            price=decimal_to_quotation(
                ((price_rub * coeff_sl_price) / schag).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * schag),
            # Цена за 1 инструмент
            stop_price=decimal_to_quotation(
                ((price_rub * coeff_sl_price) / schag).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * schag),
            # Стоп-цена заявки за 1 инструмент.
            direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
            account_id=accid,
            expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
            stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS, )
        # STOP_ORDER_TYPE_STOP_LIMIT    ИЛИ  STOP_ORDER_TYPE_STOP_LOSS print('УСТАНОВИЛИ НОВУЮ СТОП ЗАЯВКУ')
        """КОНЕЦ УСТАНАВЛИВАЕМ НОВЫЙ СТОП-ЛОСС"""
    except Exception as e:
        logger.info(f"{tiker} - moving_stop_los() ошибка передвигания СТОП-ЛОСА : Exception as e : {e}")


def resetting_stop_los(cl):  # , figi: str, tiker: str
    """ОПРЕДЕЛЯЕМ ГДЕ ПО ФАКТУ НАХОДИТСЯ ЦЕНА И В СООТВЕТСТВИИ ПЕРЕСТАВЛЯЕМ СТОП-ЛОС"""
    try:
        # Определяем цену по которой купили. Получаем информацию о позициях на счёте
        positions = cl.operations.get_portfolio(account_id=accid).positions
        for position in positions:
            if position.instrument_type == 'share':  # 'currency' для руб
                # Конвертируем MoneyValue в float (рубли). СРЕДНЯЯ ЦЕНА И КОЛИЧЕСТВО ЧТО ПОКУПАЛИ
                price_rub = float(position.average_position_price.units + position.average_position_price.nano / 1e9)
                quantity_lots_new = int(position.quantity_lots.units + position.quantity_lots.nano / 1e9)
                # Получаем текущую цену инструмента (последняя сделка)
                last_price = cl.market_data.get_last_prices(figi=[position.figi]).last_prices[0]
                current_price = float(quotation_to_decimal(last_price.price))
                # ОПРЕДЕЛЯЕМ ШАГ АКТИВА
                schag = opredelaem_schag(cl=cl, figi=position.figi, tiker=position.ticker)
                try:
                    # Функцию для определения цены стопа (уже существующего)
                    execution_price = price_active_stop_loss(cl=cl, figi=position.figi, tiker=position.ticker)
                    # УСЛОВИЯ ДЛЯ ПОДОДВИГАНИЯ СТОП-ЛОСА
                    # если цена сейчас в диапазоне(1,002 до 1,004) то стоп-лос 1,0015
                    if execution_price < price_rub * 1.002 < current_price < price_rub * 1.004:
                        coeff_sl_price = Decimal(1.0015)
                        moving_stop_los(cl=cl, figi=position.figi, tiker=position.ticker,
                                        quantity=quantity_lots_new, price_rub=Decimal(price_rub),
                                        coeff_sl_price=coeff_sl_price, schag=schag)
                        inform.info(f"{position.ticker} - ПЕРЕДВИНУЛ СТОП-ЛОС НА БЕЗУБЫТОЧНОСТЬ (0,15%)")
                    # если цена сейчас в диапазоне(1,004 до 1,008) стоп-лос 1,003
                    elif execution_price < price_rub * 1.004 <= current_price < price_rub * 1.008:
                        coeff_sl_price = Decimal(1.003)
                        moving_stop_los(cl=cl, figi=position.figi, tiker=position.ticker,
                                        quantity=quantity_lots_new, price_rub=Decimal(price_rub),
                                        coeff_sl_price=coeff_sl_price, schag=schag)
                        inform.info(f"{position.ticker} - ПЕРЕДВИНУЛ СТОП-ЛОС НА (0,3%) ")
                    # если цена сейчас в диапазоне(1,008 до 1,015) стоп-лос 1,007
                    elif execution_price < price_rub * 1.008 <= current_price < price_rub * 1.015:
                        coeff_sl_price = Decimal(1.007)
                        moving_stop_los(cl=cl, figi=position.figi, tiker=position.ticker,
                                        quantity=quantity_lots_new, price_rub=Decimal(price_rub),
                                        coeff_sl_price=coeff_sl_price, schag=schag)
                        inform.info(f"{position.ticker} - ПЕРЕДВИНУЛ СТОП-ЛОС НА (0,7%) ")
                    # если цена сейчас в диапазоне(1,015 до 1,022) стоп-лос 1,013
                    elif execution_price < price_rub * 1.015 <= current_price < price_rub * 1.022:
                        coeff_sl_price = Decimal(1.013)
                        moving_stop_los(cl=cl, figi=position.figi, tiker=position.ticker,
                                        quantity=quantity_lots_new, price_rub=Decimal(price_rub),
                                        coeff_sl_price=coeff_sl_price, schag=schag)
                        inform.info(f"{position.ticker} - ПЕРЕДВИНУЛ СТОП-ЛОС НА (1,3%) ")
                    # если цена сейчас в диапазоне(1,022 до 1,031) стоп-лос 1,02
                    elif execution_price < price_rub * 1.022 <= current_price < price_rub * 1.031:
                        coeff_sl_price = Decimal(1.02)
                        moving_stop_los(cl=cl, figi=position.figi, tiker=position.ticker,
                                        quantity=quantity_lots_new, price_rub=Decimal(price_rub),
                                        coeff_sl_price=coeff_sl_price, schag=schag)
                        inform.info(f"{position.ticker} - ПЕРЕДВИНУЛ СТОП-ЛОС НА (2%) ")
                    # если цена сейчас в диапазоне(1,031 до 1,041) стоп-лос 1,03
                    elif execution_price < price_rub * 1.031 <= current_price < price_rub * 1.041:
                        coeff_sl_price = Decimal(1.03)
                        moving_stop_los(cl=cl, figi=position.figi, tiker=position.ticker,
                                        quantity=quantity_lots_new, price_rub=Decimal(price_rub),
                                        coeff_sl_price=coeff_sl_price, schag=schag)
                        inform.info(f"{position.ticker} - ПЕРЕДВИНУЛ СТОП-ЛОС НА (3%) ")
                    # если цена сейчас в диапазоне(1,041 до 1,045) стоп-лос 1,04
                    elif execution_price < price_rub * 1.041 <= current_price < price_rub * 1.045:
                        coeff_sl_price = Decimal(1.04)
                        moving_stop_los(cl=cl, figi=position.figi, tiker=position.ticker,
                                        quantity=quantity_lots_new, price_rub=Decimal(price_rub),
                                        coeff_sl_price=coeff_sl_price, schag=schag)
                        inform.info(f"{position.ticker} - ПЕРЕДВИНУЛ СТОП-ЛОС НА (4%) ")
                    else:
                        per = round((execution_price - Decimal(price_rub)) * 100 / Decimal(price_rub), 1)
                        inform.info(f"{position.ticker} - СТОП-ЛОС ОСТАЕТСЯ как было. ({per}%)")
                except Exception as e:
                    logger.info(
                        f"{position.ticker} - resetting_stop_los() ошибка в сортировке СТОП-ЛОСА : Ex as e : {e}")
    except Exception as e:
        logger.info(f"resetting_stop_los() ошибка в самой функции: Ex as e : {e}")


# -------ФУНКЦИИ ЗАПИСИ ДАННЫХ В SQL--------

def process_sale_with_fifo(session: Session, sale: SalesInform):  # Обьявл сесс и нужн строку при продаже new_line_sale
    """Обрабатывает продажу по принципу FIFO:- находит незакрытые покупки по FIGI
    - закрывает их в порядке возрастания даты
    - рассчитывает прибыль"""
    try:
        inform.info(f"🔍 Обрабатываем продажу: {sale.tiker}, {sale.quantity_sale} шт по {sale.sale_price} ₽")
        # Получаем ВСЕ покупки этого FIGI, отсортированные по дате (FIFO)
        buys = session.query(BuyInform).filter(and_(BuyInform.figi == sale.figi, BuyInform.quantity_buy > 0)).order_by(
            asc(BuyInform.date_buy)).all()  # получаем строчки по figi где кол-во > 0
        if not buys:
            inform.info(f"❌ Нет покупок для FIGI {sale.figi} — продажа без покрытия!")
            return
        # Переменные для расчета
        remaining = sale.quantity_sale  # сколько нужно продать?
        total_buy_cost = 0.0  # сколько всего потратили на эти лоты?
        total_commission_buy = 0.0  # сколько заплатили комиссии при покупке?
        used_buys = []  # сюда запишем, какие покупки "закрыли"
        first_buy_date = None  # дата первой использованной покупки (для расчёта срока)
        # Проходим по покупкам (FIFO)
        for buy in buys:
            if remaining <= 0:
                break  # всё продали — выходим
            if buy.quantity_buy <= 0:
                continue
            taken = min(buy.quantity_buy, remaining)
            cost = taken * buy.buy_price
            commission = (taken / buy.quantity_buy) * buy.commission_buy

            total_buy_cost += cost
            total_commission_buy += commission
            # Запоминаем дату первой покупки (для time_difference_days)
            if first_buy_date is None:
                first_buy_date = buy.date_buy

            used_buys.append({
                "buy_id": buy.id,
                "date": buy.date_buy.isoformat(),
                "quantity": taken,
                "price": buy.buy_price,
                "commission_part": round(commission, 2)})

            # Уменьшаем остаток покупки
            buy.quantity_buy -= taken
            session.add(buy)  # помечаем на обновление # говорим SQLAlchemy: "эту строку нужно обновить"
            remaining -= taken
        # Проверка: продали больше, чем купили?
        if remaining > 0:
            # Продажа без покрытия — возможно, short или ошибка
            inform.info(f"⚠️ Продажа без достаточных покупок: {sale.tiker}, остаток {remaining}")
            return

        # === РАСЧЁТ ФИНАНСОВЫХ ПОКАЗАТЕЛЕЙ ===
        total_sale_amount = sale.quantity_sale * sale.sale_price  # Выручка от продажи, сколько поступило на счет
        total_commission_sale = sale.commission_sales  # Комиссия при продаже
        gross_income = total_sale_amount - total_buy_cost  # Все покупки - все продажи
        if gross_income > 0:
            # Добовляется удержание налога
            net_profit = gross_income - total_commission_buy - total_commission_sale - gross_income * 0.13
        else:
            # Налог не берется
            net_profit = gross_income - total_commission_buy - total_commission_sale
        # Условие для 13%
        is_profitable = net_profit > 0
        percent_profit = round((net_profit / total_buy_cost) * 100, 2)
        # Расчёт разницы в днях между первой покупкой и продажей
        if first_buy_date:
            time_diff = sale.date_sale - first_buy_date
            time_difference_days = time_diff.days
        else:
            time_difference_days = 0
            # === СОХРАНЕНИЕ В ТВОЮ ТАБЛИЦУ ===
        # print(type(sale.date_sale),type(time_difference_days),type(first_buy_date))
        # Моя таблица
        res_my = MyTradeResult(
            tiker=sale.tiker,
            date_sale=sale.date_sale,
            quantity_sale=sale.quantity_sale,
            buy_price=round(total_buy_cost / sale.quantity_sale, 2),  # средняя цена покупки,
            commission_buy=round(total_commission_buy, 2),
            sale_price=sale.sale_price,  # Цена покупки
            commission_sales=sale.commission_sales,  # Комиссия продажи
            income=round(total_sale_amount, 2),  # Выручка от продажи, сколько поступило на счет
            conclusion_trading="прибыль" if is_profitable else "убыток",  # продумать по лучше
            net_profit=round(net_profit, 2),
            percent_profit=percent_profit,
            time_difference_days=time_difference_days,
            # zero_point=buy.buy_price * 1.00092,  # Точка окупаемости
            # conclusion_bool=is_profitable,
            figi=sale.figi,
            date_buy=first_buy_date)
        session.add(res_my)
        session.commit()
        inform.info(f"✅ Сделка закрыта: прибыль = {net_profit:.2f} ₽ ({percent_profit}%)")
    except Exception as e:
        logger.info(f"process_sale_with_fifo() ошибка в обработке продажи по FIFO: Ex as e : {e}")


def trading_information(cl, days: int, tm=2):
    """ЗАПРАШИВАЕТ ИНФОРМАЦИЮ ЗА days ДНЯ О ПОКУПКЕ ,ПРОДАЖЕ И ЗАПИСЫВАЕТ В SQL"""
    try:
        operations = cl.operations.get_operations(
            account_id=accid,  # Указываем счёт
            from_=datetime.now(UTC) - timedelta(days=days),  # За последние 3 дня
            to=datetime.now(UTC),  # datetime(2025, 12, 25, 0, 0, 0)
            state=OperationState.OPERATION_STATE_EXECUTED, )
        for operate in operations.operations:
            if operate.operation_type == OperationType.OPERATION_TYPE_BUY:  # Фильтруем по покупке
                operatio_type = "покупка"
                date_buy = operate.date  # С датой нужно разобраться, стоит ли делать +5 часов
                figi = operate.figi
                instruments: InstrumentsService = cl.instruments
                tiker = instruments.share_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                                             id=operate.figi).instrument.ticker
                quantity_buy = int(operate.quantity)
                buy_price = float(operate.price.units + operate.price.nano / 1e9)
                commission_buy = abs(
                    round(operate.child_operations[0].payment.units + operate.child_operations[0].payment.nano / 1e9,
                          2))
                time.sleep(tm)
                # Проверяем есть ли в базе BuyInform. Архив может и содержать дубли
                existing = session.query(BuyInform).filter(
                    BuyInform.tiker == tiker,
                    BuyInform.date_buy == date_buy.replace(microsecond=0),
                    BuyInform.buy_price == buy_price).first()
                if existing:
                    pass
                    # inform.info(f"💰 Покупка {tiker} от {date_buy.replace(microsecond=0)} уже в базе — пропускаем.")
                else:
                    new_line_buy = BuyInform(date_buy=date_buy.replace(microsecond=0), tiker=tiker,
                                             operatio_type=operatio_type, quantity_buy=quantity_buy,
                                             buy_price=buy_price,
                                             commission_buy=commission_buy, figi=figi)
                    archive_new_line_buy = ArchiveBuyInform(date_buy=date_buy.replace(microsecond=0), tiker=tiker,
                                                            operatio_type=operatio_type, quantity_buy=quantity_buy,
                                                            buy_price=buy_price, commission_buy=commission_buy,
                                                            figi=figi)
                    try:
                        session.add(new_line_buy)
                        session.add(archive_new_line_buy)
                        session.commit()
                    except IntegrityError as e:
                        session.rollback()  # откатываем попытку добавления
                        # logger.info(f"{tiker} - ЗАПИСЬ СУЩЕСТВУЕТ: Exception as e : {e}")
            elif operate.operation_type == OperationType.OPERATION_TYPE_SELL:  # Фильтруем по продажи
                # # id_prodaga = operate.id
                # # trade_id = operate.trades[0].trade_id
                operatio_type = "продажа"
                date_sale = operate.date
                figi = operate.figi
                instruments: InstrumentsService = cl.instruments
                tiker = instruments.share_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                                             id=operate.figi).instrument.ticker
                quantity_sale = int(operate.quantity)
                sale_price = float(operate.price.units + operate.price.nano / 1e9)
                commission_sales = abs(
                    round(operate.child_operations[0].payment.units + operate.child_operations[0].payment.nano / 1e9,
                          2))
                time.sleep(tm)
                # Проверяем есть ли в базе
                existing = session.query(SalesInform).filter(
                    SalesInform.tiker == tiker,
                    SalesInform.date_sale == date_sale.replace(microsecond=0),
                    SalesInform.sale_price == sale_price).first()
                if existing:
                    pass
                    # inform.info(f"💰 Продажа {tiker} от {date_sale.replace(microsecond=0)} уже в базе — пропускаем.")
                else:
                    new_line_sale = SalesInform(date_sale=date_sale.replace(microsecond=0), tiker=tiker,
                                                operatio_type=operatio_type, quantity_sale=quantity_sale,
                                                sale_price=sale_price,
                                                commission_sales=commission_sales, figi=figi)
                    try:
                        session.add(new_line_sale)
                        session.commit()
                        # ⚡ Сразу обрабатываем FIFO
                        process_sale_with_fifo(session, new_line_sale)
                    except IntegrityError as e:
                        session.rollback()  # откатываем попытку добавления
                        # logger.info(f"{tiker} - ЗАПИСЬ СУЩЕСТВУЕТ: Exception as e : {e}")
    except Exception as e:
        logger.info(f"trading_information() ошибка сбор информации о покупке и продаже: Ex as e : {e}")


# -------ОТПРАВКА В ТЕЛЕГРАММ--------
def send_telegram(tupl: tuple,
                  telegram_cl=TelegramClient(name="SEM", api_id=api_iddd, api_hash=telegtok,
                                             parse_mode=ParseMode.HTML), group=groupt):
    """ОТПРАВЛЯЕТ В ТЕЛЕГРАММ НА ПОКУПКУ И ПРОДАЖУ"""
    try:
        with telegram_cl:
            telegram_cl.send_message(group, f"-----НАЧАЛО : {datetime.now().strftime('%d.%m.%Y %H:%M')}-----")
            if tupl[0]:
                telegram_cl.send_message(group, f"✅ ПОКУПКА : <b>{tupl[0].keys()}</b>")
            time.sleep(1)
            if tupl[1]:
                telegram_cl.send_message(group, f"🔴 ПРОДАЖА : <b>{tupl[1].keys()}</b>")
            end_time_str = (datetime.now() + timedelta(seconds=900)).strftime("%d.%m.%Y %H:%M")
            telegram_cl.send_message(group, f"-----СЛЕДУЮЩИЙ : {end_time_str}-----")
            telegram_cl.send_message(group, "🧠")
    except Exception as e:
        logger.info(f"send_telegram() ошибка в телеграмм: Ex as e : {e}")


if __name__ == "__main__":
    ...
