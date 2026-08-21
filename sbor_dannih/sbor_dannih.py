import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from t_tech.invest import CandleInterval, Client
from t_tech.invest.utils import decimal_to_quotation, now, quotation_to_decimal

from ta.momentum import RSIIndicator  # , MACD
from ta.trend import SMAIndicator  # Раскомментируйте ваши импорты ta
from ta.volatility import BollingerBands

from log.logger import logger
# from tinkoff.invest import CandleInterval

# Загружаем переменные окружения
load_dotenv("../terminator/.env.term")


# @dataclass
# class IndicatorData:
#     """Структура для хранения рассчитанных индикаторов"""
#
#     last_rsi: float
#     prev_rsi: float
#     prev_rsi_3: float
#     prev_rsi_4: float
#     last_macd: float
#     prev_macd: float
#     prev_macd_3: float
#     prev_macd_4: float
#     last_sma_10_1: float
#     last_sma_10_2: float
#     last_sma_10_3: float
#     last_sma_10_4: float
#     close: float
#     mid_bollinger: float
#     volume: float
#     mean_volume: float


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
