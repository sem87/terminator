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
        self.buy_day = {}
        self.buy_hour = {}
        self.buy_15min = {}
        self.buy_itog = {}
        self.sale_day = {}
        self.sale_hour = {}
        self.sale_15min = {}
        self.sale_itog = {}


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

    def filter_list(self, interval: CandleInterval, figi: str, tiker: str, data: IndicatorData):
        """Фильтр по спискам на покупку и продажу"""
        try:
            # Примечание: buy_day, sale_day, FilterTickerDict, session и др.
            # должны быть доступны в глобальной области видимости или импортированы.
            interval_map = {
                CandleInterval.CANDLE_INTERVAL_DAY: ("day", buy_day, sale_day),  # type: ignore
                CandleInterval.CANDLE_INTERVAL_HOUR: ("hour", buy_hour, sale_hour),  # type: ignore
                CandleInterval.CANDLE_INTERVAL_5_MIN: ("5_min", buy_5min, sale_5min)
            }

            if interval not in interval_map:
                logger.info(f"{tiker} - filter_list() - НЕТ НУЖНОГО ИНТЕРВАЛА")
                return

            timeframe, buy_dict, sale_dict = interval_map[interval]

            def add_signal(action: str, strategy: str, target_dict: dict):
                target_dict[tiker] = figi
                filter_tiker = FilterTickerDict(  # type: ignore
                    tiker=tiker,
                    timeframe=timeframe,
                    action=action,
                    strategy=f"{strategy}_{timeframe}",
                    description=f"last_MACD:{round(data.last_macd, 2)}, last_rsi:{round(data.last_rsi, 2)}, midBoll:{round(data.mid_bollinger, 2)}",
                )
                session.add(filter_tiker)  # type: ignore
                session.commit()  # type: ignore

            # Предварительный расчет общих условий для читаемости и производительности
            sma_up = data.last_sma_10_3 < data.last_sma_10_2 < data.last_sma_10_1
            sma_down = data.last_sma_10_1 < data.last_sma_10_2 < data.last_sma_10_3
            close_below_boll = data.close < data.mid_bollinger
            close_above_boll = data.close > data.mid_bollinger

            # --- ЛОГИКА ДЛЯ DAY ---
            if interval == CandleInterval.CANDLE_INTERVAL_DAY:
                if sma_up:
                    add_signal("buy", "1_buy) возраст SMA 10", buy_dict)
                elif sma_down:
                    add_signal("sell", "1_sell) убывающий SMA 10", sale_dict)

            # --- ЛОГИКА ДЛЯ HOUR ---
            elif interval == CandleInterval.CANDLE_INTERVAL_HOUR:
                if sma_up and (data.prev_rsi < data.last_rsi < 65):
                    add_signal("buy", "1_buy) возраст SMA 10, RSI<65", buy_dict)
                elif sma_down and (35 < data.last_rsi < data.prev_rsi):
                    add_signal("sell", "1_sell) убывающий SMA 10, RSI>35", sale_dict)

            # --- ЛОГИКА ДЛЯ 5_MIN ---
            elif interval == CandleInterval.CANDLE_INTERVAL_5_MIN:
                # Покупка
                if close_below_boll and data.prev_macd_3 < data.prev_macd_4 and data.prev_macd_3 < data.prev_macd < data.last_macd < 0 and data.prev_rsi < data.last_rsi < 50:
                    add_signal("buy", "1_buy) нижняя т. MACD", buy_dict)
                elif close_below_boll and data.prev_macd_3 < data.prev_macd < data.last_macd < 0 and data.prev_rsi < data.last_rsi < 50:
                    add_signal("buy", "2_buy) возраст MACD", buy_dict)
                elif close_below_boll and sma_up and data.prev_rsi < data.last_rsi < 55:
                    add_signal("buy", "3_buy) возраст SMA10, боллинджер огранич.", buy_dict)
                elif sma_up and data.prev_rsi < data.last_rsi < 50:
                    add_signal("buy", "4_buy) возраст SMA10 и rsi < 50", buy_dict)
                elif close_below_boll and data.prev_macd < data.prev_macd_3 and data.prev_macd < data.last_macd < 0 and data.prev_rsi < data.last_rsi < 50:
                    add_signal("buy", "5_buy) нижняя т. MACD (эксп.)", buy_dict)

                # Продажа
                elif close_above_boll and data.prev_macd_4 < data.prev_macd_3 and 0 < data.last_macd < data.prev_macd < data.prev_macd_3 and 50 < data.last_rsi < data.prev_rsi:
                    add_signal("sell", "1_sell) верхняя т. MACD", sale_dict)
                elif close_above_boll and 0 < data.last_macd < data.prev_macd < data.prev_macd_3 and 50 < data.last_rsi < data.prev_rsi:
                    add_signal("sell", "2_sell) убывающий MACD", sale_dict)
                elif close_above_boll and sma_down and 45 < data.last_rsi < data.prev_rsi:
                    add_signal("sell", "3_sell) убывающий SMA10, боллинджер огранич.", sale_dict)
                elif sma_down and 50 < data.last_rsi < data.prev_rsi:
                    add_signal("sell", "4_sell) убывающий SMA10 и rsi > 50", sale_dict)
                elif close_above_boll and data.prev_macd_3 < data.prev_macd and 0 < data.last_macd < data.prev_macd and 50 < data.last_rsi < data.prev_rsi:
                    add_signal("sell", "5_sell) верхняя т. MACD (эксп.)", sale_dict)

        except Exception as e:
            logger.error(f"{tiker} - filter_list() ошибка: {e}")

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
