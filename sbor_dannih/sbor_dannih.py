import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from t_tech.invest import CandleInterval, Client
from t_tech.invest.utils import decimal_to_quotation, now, quotation_to_decimal

from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator , MACD # Раскомментируйте ваши импорты ta
from ta.volatility import BollingerBands
from typing import Optional
from log.logger import logger
# from tinkoff.invest import CandleInterval

# Загружаем переменные окружения
load_dotenv("../terminator/.env.term")


@dataclass
class IndicatorData:
    """Структура для хранения рассчитанных индикаторов"""
    # тип <class 'sbor_dannih.sbor_dannih.IndicatorData'>
    last_rsi: float
    prev_rsi: float
    prev_rsi_3: float
    prev_rsi_4: float
    last_macd: float
    prev_macd: float
    prev_macd_3: float
    prev_macd_4: float
    last_sma_10_1: float
    last_sma_10_2: float
    last_sma_10_3: float
    last_sma_10_4: float
    close: float
    mid_bollinger: float  # Исправлена опечатка (было midle)
    volume: float
    mean_volume: float



class SborDannih:
    """КЛАСС СОБИРАЕТ ДАННЫЕ"""
    def __init__(self) -> None:
        self.token = os.getenv("TOKSELL")
        self._client = None  # Сам канал
        self._services = None  # Объект Services с методами API (instruments, orders и т.д.)


    def __enter__(self):
        # Инициализация происходит здесь, при входе в контекст
        self._client = Client(self.token)
        self._services = self._client.__enter__()
        print(f"======= Клиент - {self._client }")
        print(f"======= Сервис - {self._services}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ПРАВИЛЬНОЕ ЗАКРЫТИЕ КАНАЛА"""
        if self._client is not None:
            self._client.__exit__(exc_type, exc_val, exc_tb)
            self._client = None
            self._services = None


    def cleaning_dict(self):
        pass


    #  =========================================================


    def candl(self, day: int, interval: CandleInterval, figi: str, tiker: str) -> pd.DataFrame:
        """ИЗВЛЕКАЕТ ДАННЫЕ ИЗ СВЕЧЕК ЗА ОПРЕДЕЛЕННЫЙ ПЕРИОД"""
        try:
            print(f"======= Клиент - {self._client}")
            print(f"======= Сервис - {self._services}")
            # self.cleaning_dict() - нужно не забыть чистить словари и делать это правильно
            # Получаем данные о свечах указываем интервал
            candle_data =  self._services.market_data.get_candles(
                figi=figi,
                from_=now() - timedelta(days=day),  # было day=1 (неверно)
                to=now(),  # было datetime.UTC() (неверно)
                interval=interval,
            )  # '''CandleInterval.CANDLE_INTERVAL_15_MIN  # нужно указать конкретный интервал'''
            # Преобразуем в удобный формат
            candles = []
            for candle in candle_data.candles:
                candles.append(
                    {
                        "Время": candle.time.strftime("%Y-%m-%d %H:%M:%S"),
                        "Открытие": candle.open.units + candle.open.nano / 1e9,
                        "МАХ": candle.high.units + candle.high.nano / 1e9,
                        "MIN": candle.low.units + candle.low.nano / 1e9,
                        "Закрытие": candle.close.units + candle.close.nano / 1e9,
                        "Объем": candle.volume,
                    }
                )
            # Создаем DataFrame для красивого отображения
            df = pd.DataFrame(candles)
            return df
        except Exception as e:
            logger.info(f"{tiker} - candl() извлечение данных : {interval},период : {day} , Exception as e : {e}")
            df = pd.DataFrame(None)
            # Проверить когда пустой Дата фрейм???
            return df



    def calculate_indicator(self, df: pd.DataFrame, tiker: str) -> Optional[IndicatorData]:
        """Рассчитывает технические индикаторы для DataFrame"""
        try:
            # 1. Безопасная копия
            work_df = df.copy()
            # print(work_df.all())
            work_df["Время"] = pd.to_datetime(work_df["Время"])
            work_df.set_index("Время", inplace=True)

            # 2. Расчет индикаторов (библиотека ta)
            work_df["SMA_10"] = SMAIndicator(close=work_df["Закрытие"], window=10).sma_indicator()
            work_df["RSI"] = RSIIndicator(close=work_df["Закрытие"], window=14).rsi()
            work_df["MACD_Hist"] = MACD(
                close=work_df["Закрытие"], window_slow=26, window_fast=12, window_sign=9
            ).macd_diff()
            work_df["bb_middle"] = BollingerBands(
                close=work_df["Закрытие"], window=20, window_dev=2
            ).bollinger_mavg()

            # 3. Формирование и возврат результата (имена полей строго совпадают с IndicatorData)
            return IndicatorData(
                last_rsi=float(work_df["RSI"].iloc[-1]),
                prev_rsi=float(work_df["RSI"].iloc[-2]),
                prev_rsi_3=float(work_df["RSI"].iloc[-3]),
                prev_rsi_4=float(work_df["RSI"].iloc[-4]),
                last_macd=float(work_df["MACD_Hist"].iloc[-1]),
                prev_macd=float(work_df["MACD_Hist"].iloc[-2]),
                prev_macd_3=float(work_df["MACD_Hist"].iloc[-3]),
                prev_macd_4=float(work_df["MACD_Hist"].iloc[-4]),
                last_sma_10_1=float(work_df["SMA_10"].iloc[-1]),
                last_sma_10_2=float(work_df["SMA_10"].iloc[-2]),
                last_sma_10_3=float(work_df["SMA_10"].iloc[-3]),
                last_sma_10_4=float(work_df["SMA_10"].iloc[-4]),
                close=float(work_df["Закрытие"].iloc[-1]),
                mid_bollinger=float(work_df["bb_middle"].iloc[-1]),
                volume=float(work_df["Объем"].iloc[-1]),
                mean_volume=float(work_df["Объем"].iloc[-10:].mean()),

            )

        except Exception as e:
            logger.error(f"{tiker} - calculate_indicator() ошибка: {e}")
            return None

    def filter_list(interval, figi: str, tiker: str, tuple_indicator: tuple):
        """ФИЛЬТР ПО СПИСКАМ НА ПОКУПКУ И ПРОДАЖУ"""
        try:
            if interval == CandleInterval.CANDLE_INTERVAL_DAY:
                """ДНЕВНОЙ ИНТЕРВАЛ УСЛОВИЕ"""
                timeframe = "day"
                # ПОКУПКА
                # 1_buy_day) возраст SMA10
                # last_sma_10_3<last_sma_10_2<last_sma_10_1)
                if tuple_indicator[10] < tuple_indicator[9] < tuple_indicator[8]:
                    """ВОЗРОСТАНИЕ SMA 10 """
                    buy_day[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="buy",
                        strategy=f"1_buy_{timeframe}) возраст SMA 10",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # ПРОДАЖА
                # 1_sell_day) убывающий SMA10
                # (last_sma_10_1<last_sma_10_2<last_sma_10_3
                elif tuple_indicator[8] < tuple_indicator[9] < tuple_indicator[10]:
                    """УБЫВАЮЩИЙ SMA 10 """
                    sale_day[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="sell",
                        strategy=f"1_sell_{timeframe}) убывающий SMA 10",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                else:
                    """НИ КУДА НЕ ПОПАЛО"""
                    pass
            elif interval == CandleInterval.CANDLE_INTERVAL_HOUR:
                """ЧАСОВОЙ ИНТЕРВАЛ УСЛОВИЕ"""
                timeframe = "hour"
                # ПОКУПКА
                # 1_buy_hour) возраст SMA 10.RSI<65    МАКСИМАЛЬНО УЖЕСТОЧИТЬ
                # (last_sma_10_3 < last_sma_10_2 < last_sma_10_1) and (prev_rsi < last_rsi < 65)
                if (tuple_indicator[10] < tuple_indicator[9] < tuple_indicator[8]) and (
                        tuple_indicator[1] < tuple_indicator[0] < 65
                ):
                    """ВОЗРОСТАНИЕ SMA 10 , RSI"""
                    buy_hour[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="buy",
                        strategy=f"1_buy_{timeframe}) возраст SMA 10.RSI<65 ",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # ПРОДАЖА
                # 1_sell_hour) убывающий SMA 10.RSI>25 '-_   МАКСИМАЛЬНО УЖЕСТОЧИТЬ
                # (last_sma_10_1  < last_sma_10_2 < last_sma_10_3) and (35<last_rsi<prev_rsi)
                elif (tuple_indicator[8] < tuple_indicator[9] < tuple_indicator[10]) and (
                        35 < tuple_indicator[0] < tuple_indicator[1]
                ):
                    """УБЫВАЮЩИЙ SMA 10 , RSI"""
                    sale_hour[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="sell",
                        strategy=f"1_sell_{timeframe}) убывающий SMA 10.RSI>35 ",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                else:
                    """НИ КУДА НЕ ПОПАЛО"""
                    pass
            elif interval == CandleInterval.CANDLE_INTERVAL_5_MIN:
                """5 МИНУТНЫЙ ИНТЕРВАЛ УСЛОВИЕ"""
                timeframe = "5_min"
                # ПОКУПКА
                # 1_buy_5_min) нижняя т MACD. -_-'
                # (цена закрытия < средняя боллинджера) and (prev_MACD_3 < prev_MACD_4) and
                # (prev_MACD_3<prev_MACD<last_MACD<0) and (prev_rsi<last_rsi<50)
                if (
                        (tuple_indicator[12] < tuple_indicator[13])
                        and (tuple_indicator[6] < tuple_indicator[7])
                        and (tuple_indicator[6] < tuple_indicator[5] < tuple_indicator[4] < 0)
                        and (tuple_indicator[1] < tuple_indicator[0] < 50)
                ):
                    "ОТБИРАЕМ В САМОМ НИЗУ 5 МИН"
                    buy_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="buy",
                        strategy=f"1_buy_{timeframe}) нижняя т MACD. -_-'",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # 2_buy_5_min) возраст MACD. _-'
                # (цена закрытия < средняя боллинджера) and
                # (prev_MACD_3<prev_MACD<last_MACD<0) and (prev_rsi<last_rsi<50)
                elif (
                        (tuple_indicator[12] < tuple_indicator[13])
                        and (tuple_indicator[6] < tuple_indicator[5] < tuple_indicator[4] < 0)
                        and (tuple_indicator[1] < tuple_indicator[0] < 50)
                ):
                    "ОТБИРАЕМ В САМОМ НИЗУ 5 МИН ПОСЛЕДУЮШИЕ СВЕЧИ MACD УВЕЛИЧИВАЮТСЯ НО <0"
                    buy_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="buy",
                        strategy=f"2_buy_{timeframe}) возраст MACD. _-'",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # 3_buy_5_min) возраст SMA10 но боллинжер огранич"   (но похоже это редкие случаи)
                # (цена закрытия < средняя боллинджера) and
                # (last_sma_10_3<last_sma_10_2<last_sma_10_1) and (prev_rsi<last_rsi<55)
                elif (
                        (tuple_indicator[12] < tuple_indicator[13])
                        and (tuple_indicator[10] < tuple_indicator[9] < tuple_indicator[8])
                        and (tuple_indicator[1] < tuple_indicator[0] < 55)
                ):
                    "SMA 10 ВОЗРАСТАЕТ НО БОЛЛИНДЖЕР ОГРАНИЧИВАЕТ"
                    buy_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="buy",
                        strategy=f"3_buy_{timeframe}) возраст SMA10 но боллинжер огранич",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # 4_buy_5_min) возраст SMA10 и rsi < 50. (ЕСЛИ УВЕЛИЧИВАТЬ ЭТО ЧИСЛО ТО МОЖЕТ МНОГО НЕУДАЧ!!)
                # (last_sma_10_3<last_sma_10_2<last_sma_10_1) and (prev_rsi<last_rsi<50)
                elif (tuple_indicator[10] < tuple_indicator[9] < tuple_indicator[8]) and (
                        tuple_indicator[1] < tuple_indicator[0] < 50
                ):
                    "SMA 10 ВОЗРАСТАЕТ"
                    buy_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="buy",
                        strategy=f"4_buy_{timeframe}) возраст SMA10 и rsi < 50.",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # 5_buy_5_min) нижняя т MACD. -_-
                # (цена закрытия < средняя боллинджера) and (prev_MACD < prev_MACD_3) and
                # (prev_MACD<last_MACD<0) and (prev_rsi<last_rsi<50)
                elif (
                        (tuple_indicator[12] < tuple_indicator[13])
                        and (tuple_indicator[5] < tuple_indicator[6])
                        and (tuple_indicator[5] < tuple_indicator[4] < 0)
                        and (tuple_indicator[1] < tuple_indicator[0] < 50)
                ):
                    "ОТБИРАЕМ В САМОМ НИЗУ 5 МИН ЭКСПЕРИМЕНТ"
                    buy_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="buy",
                        strategy=f"5_buy_{timeframe}) нижняя т MACD. -_-",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # ПРОДАЖА
                # 1_sell_5_min) верхняя т. MACD. -'-_
                # (средняя боллинджера < цена закрытия) and (prev_MACD_4 < prev_MACD_3) and
                # (0<last_MACD<prev_MACD<prev_MACD_3) and (50<last_rsi<prev_rsi)
                elif (
                        (tuple_indicator[13] < tuple_indicator[12])
                        and (tuple_indicator[7] < tuple_indicator[6])
                        and (0 < tuple_indicator[4] < tuple_indicator[5] < tuple_indicator[6])
                        and (50 < tuple_indicator[0] < tuple_indicator[1])
                ):
                    "ОТБИРАЕМ В САМОМ ВЕРХУ 5 МИН"
                    sale_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="sell",
                        strategy=f"1_sell_{timeframe}) верхняя т. MACD. -'-_",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # 2_sell_5_min) убывающий MACD '-_
                # (средняя боллинджера < цена закрытия) and
                # (0<last_MACD<prev_MACD<prev_MACD_3) and (50<last_rsi<prev_rsi)
                elif (
                        (tuple_indicator[13] < tuple_indicator[12])
                        and (0 < tuple_indicator[4] < tuple_indicator[5] < tuple_indicator[6])
                        and (50 < tuple_indicator[0] < tuple_indicator[1])
                ):
                    "ОТБИРАЕМ В САМОМ ВЕРХУ 5 МИН ПОСЛЕДУЮШИЕ СВЕЧИ MACD МОЖЕТ > 0"
                    sale_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="sell",
                        strategy=f"2_sell_{timeframe}) убывающий MACD '-_",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # 3_sell_5_min) убывающий SMA10 но боллинжер ограничивает."   (но похоже это редкие случаи)
                # (средняя боллинджера < цена закрытия) and
                # (last_sma_10_1<last_sma_10_2<last_sma_10_3) and (45<last_rsi<prev_rsi)
                elif (
                        (tuple_indicator[13] < tuple_indicator[12])
                        and (tuple_indicator[8] < tuple_indicator[9] < tuple_indicator[10])
                        and (45 < tuple_indicator[0] < tuple_indicator[1])
                ):
                    "SMA 10 УБЫВАЕТ НО БОЛЛИНДЖЕР ОГРАНИЧИВАЕТ"
                    sale_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="sell",
                        strategy=f"3_sell_{timeframe}) убывающий SMA10 но боллинжер ограничивает.",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # 4_sell_5_min) убывающий SMA10 и rsi > 60 (ЕСЛИ уменьшать ЭТО ЧИСЛО ТО МОЖЕТ МНОГО НЕУДАЧ!!!!)
                # (last_sma_10_1<last_sma_10_2<last_sma_10_3) and (50<last_rsi<prev_rsi)
                elif (tuple_indicator[8] < tuple_indicator[9] < tuple_indicator[10]) and (
                        50 < tuple_indicator[0] < tuple_indicator[1]
                ):
                    "SMA 10 УБЫВАЕТ"
                    sale_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="sell",
                        strategy=f"4_sell_{timeframe}) убывающий SMA10 и rsi > 50",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                # 5_sell_5_min) верхняя т. MACD. -'-
                # (средняя боллинджера < цена закрытия) and (prev_MACD_3 < prev_MACD) and
                # (0<last_MACD<prev_MACD) and (50<last_rsi<prev_rsi)
                elif (
                        (tuple_indicator[13] < tuple_indicator[12])
                        and (tuple_indicator[6] < tuple_indicator[5])
                        and (0 < tuple_indicator[4] < tuple_indicator[5])
                        and (50 < tuple_indicator[0] < tuple_indicator[1])
                ):
                    "ОТБИРАЕМ В САМОМ ВЕРХУ 5 МИН ЭКСПЕРИМЕНТ"
                    sale_15min[tiker] = figi
                    filter_tiker = FilterTickerDict(
                        tiker=tiker,
                        timeframe=timeframe,
                        action="sell",
                        strategy=f"5_sell_{timeframe}) верхняя т. MACD. -'-",
                        description=f"last_MACD:{round(tuple_indicator[4], 2)}, last_rsi:{round(tuple_indicator[0], 2)}, midBoll:{round(tuple_indicator[13], 2)}",
                    )
                    session.add(filter_tiker)
                    session.commit()
                else:
                    """НИ КУДА НЕ ПОПАЛО"""
                    pass
            else:
                logger.info(f"{tiker} - filter_list() - НЕТ НУЖНОГО ИНТЕРВАЛА")
        except Exception as e:
            logger.info(f"{tiker} - filter_list() ошибка записи в список : Exception as e : {e}")

    #  =========================================================


    @property
    def client(self):
        """ЛЕНИВОЕ СОЗДАНИЕ КЛИЕНТА И ПОЛУЧЕНИЕ SERVICES"""
        if self._services is None:
            self._client = Client(self.token)
            # __enter__ открывает канал и возвращает объект Services
            self._services = self._client.__enter__()
        return self._services



    def __str__(self):
        return f"ЭТО КЛАСС СБОР ДАННЫХ"


if __name__ == "__main__":
    pass
