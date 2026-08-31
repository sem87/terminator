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
from ta.trend import SMAIndicator, MACD  # Раскомментируйте ваши импорты ta
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
        # Словари для промежуточных результатов (если нужны)
        self.buy_day = {}
        self.buy_hour = {}
        self.buy_5min = {}  # Было buy_15min, исправлено под логику 5 мин

        self.sale_day = {}
        self.sale_hour = {}
        self.sale_5min = {}  # Было sale_15min


        # Итоговые словари для конфлюенса отбора в телеграм
        self.buy_itog_d_h = {}
        self.sale_itog_d_h = {}
        # Итоговые словари для конфлюенса
        self.buy_itog = {}
        self.sale_itog = {}

    def __enter__(self):
        # Инициализация происходит здесь, при входе в контекст
        self._client = Client(self.token)
        self._services = self._client.__enter__()
        print(f"======= Клиент - {self._client}")
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
            # self.cleaning_dict() - нужно не забыть чистить словари и делать это правильно
            # Получаем данные о свечах указываем интервал
            candle_data = self._services.market_data.get_candles(
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

    def _evaluate_timeframe(self, tf_name: str, data: IndicatorData) -> tuple[bool, bool, str]:
        """Оценивает сигналы для одного таймфрейма. Возвращает (is_buy, is_sell, description)"""
        sma_up = data.last_sma_10_3 < data.last_sma_10_2 < data.last_sma_10_1
        sma_down = data.last_sma_10_1 < data.last_sma_10_2 < data.last_sma_10_3
        close_below_boll = data.close < data.mid_bollinger
        close_above_boll = data.close > data.mid_bollinger

        is_buy, is_sell = False, False
        desc = ""

        if tf_name == "day":
            if sma_up:
                is_buy, desc = True, "SMA 10 растет"
            elif sma_down:
                is_sell, desc = True, "SMA 10 падает"

        elif tf_name == "hour":
            if sma_up and (data.prev_rsi < data.last_rsi < 65):
                is_buy, desc = True, "SMA 10 растет, RSI<65"
            elif sma_down and (35 < data.last_rsi < data.prev_rsi):
                is_sell, desc = True, "SMA 10 падает, RSI>35"

        elif tf_name == "5_min":
            # Условия на покупку (любое из 5)
            buy_conds = [
                close_below_boll and data.prev_macd_3 < data.prev_macd_4 and data.prev_macd_3 < data.prev_macd < data.last_macd < 0 and data.prev_rsi < data.last_rsi < 50,
                close_below_boll and data.prev_macd_3 < data.prev_macd < data.last_macd < 0 and data.prev_rsi < data.last_rsi < 50,
                close_below_boll and sma_up and data.prev_rsi < data.last_rsi < 55,
                sma_up and data.prev_rsi < data.last_rsi < 50,
                close_below_boll and data.prev_macd < data.prev_macd_3 and data.prev_macd < data.last_macd < 0 and data.prev_rsi < data.last_rsi < 50
            ]
            if any(buy_conds):
                is_buy, desc = True, "Сигнал 5мин на покупку (MACD/RSI/BB)"

            # Условия на продажу (любое из 5)
            sell_conds = [
                close_above_boll and data.prev_macd_4 < data.prev_macd_3 and 0 < data.last_macd < data.prev_macd < data.prev_macd_3 and 50 < data.last_rsi < data.prev_rsi,
                close_above_boll and 0 < data.last_macd < data.prev_macd < data.prev_macd_3 and 50 < data.last_rsi < data.prev_rsi,
                close_above_boll and sma_down and 45 < data.last_rsi < data.prev_rsi,
                sma_down and 50 < data.last_rsi < data.prev_rsi,
                close_above_boll and data.prev_macd_3 < data.prev_macd and 0 < data.last_macd < data.prev_macd and 50 < data.last_rsi < data.prev_rsi
            ]
            if any(sell_conds):
                is_sell, desc = True, "Сигнал 5мин на продажу (MACD/RSI/BB)"

        return is_buy, is_sell, desc

    def check_confluence(self, figi: str, tiker: str,
                         data_day: IndicatorData,
                         data_hour: IndicatorData,
                         data_5min: IndicatorData):
        """Проверяет одновременное выполнение условий на Day, Hour и 5min"""
        try:
            # 1. Оцениваем каждый таймфрейм отдельно
            buy_d, sell_d, desc_d = self._evaluate_timeframe("day", data_day)
            buy_h, sell_h, desc_h = self._evaluate_timeframe("hour", data_hour)
            buy_m, sell_m, desc_m = self._evaluate_timeframe("5_min", data_5min)

            # 2. Проверяем строгий конфлюенс (все 3 должны быть True)
            if buy_d and buy_h and buy_m:
                self.buy_itog[tiker] = {
                    "figi": figi,
                    "action": "buy",
                    "strategy": "CONFLUENCE_BUY_3TF",
                    "description": f"Day: {desc_d} | Hour: {desc_h} | 5m: {desc_m}",
                    "indicators": {
                        "day": {"rsi": round(data_day.last_rsi, 2), "sma": round(data_day.last_sma_10_1, 2)},
                        "hour": {"rsi": round(data_hour.last_rsi, 2), "sma": round(data_hour.last_sma_10_1, 2)},
                        "5min": {"rsi": round(data_5min.last_rsi, 2), "macd": round(data_5min.last_macd, 4),
                                 "boll": round(data_5min.mid_bollinger, 2)}
                    }
                }
                logger.info(f"✅ {tiker} - КОНФЛЮЕНС НА ПОКУПКУ (Day, Hour, 5m)")

            elif sell_d and sell_h and sell_m:
                self.sale_itog[tiker] = {
                    "figi": figi,
                    "action": "sell",
                    "strategy": "CONFLUENCE_SELL_3TF",
                    "description": f"Day: {desc_d} | Hour: {desc_h} | 5m: {desc_m}",
                    "indicators": {
                        "day": {"rsi": round(data_day.last_rsi, 2), "sma": round(data_day.last_sma_10_1, 2)},
                        "hour": {"rsi": round(data_hour.last_rsi, 2), "sma": round(data_hour.last_sma_10_1, 2)},
                        "5min": {"rsi": round(data_5min.last_rsi, 2), "macd": round(data_5min.last_macd, 4),
                                 "boll": round(data_5min.mid_bollinger, 2)}
                    }
                }
                logger.info(f"✅ {tiker} - КОНФЛЮЕНС НА ПРОДАЖУ (Day, Hour, 5m)")

            #==========Для телеграмма молния =============
            elif buy_d and buy_h :
                self.buy_itog[tiker] = {
                    "figi": figi,
                    "action": "buy",
                    "strategy": "CONFLUENCE_BUY_3TF",
                    "description": f"Day: {desc_d} | Hour: {desc_h} | 5m: {desc_m}",
                    "indicators": {
                        "day": {"rsi": round(data_day.last_rsi, 2), "sma": round(data_day.last_sma_10_1, 2)},
                        "hour": {"rsi": round(data_hour.last_rsi, 2), "sma": round(data_hour.last_sma_10_1, 2)},
                        "5min": {"rsi": round(data_5min.last_rsi, 2), "macd": round(data_5min.last_macd, 4),
                                 "boll": round(data_5min.mid_bollinger, 2)}
                    }
                }
                logger.info(f"✅ {tiker} - ТЕЛЕГА НА ПОКУПКУ (Day, Hour)")
            elif sell_d and sell_h and sell_m:
                self.sale_itog[tiker] = {
                    "figi": figi,
                    "action": "sell",
                    "strategy": "CONFLUENCE_SELL_3TF",
                    "description": f"Day: {desc_d} | Hour: {desc_h} | 5m: {desc_m}",
                    "indicators": {
                        "day": {"rsi": round(data_day.last_rsi, 2), "sma": round(data_day.last_sma_10_1, 2)},
                        "hour": {"rsi": round(data_hour.last_rsi, 2), "sma": round(data_hour.last_sma_10_1, 2)},
                        "5min": {"rsi": round(data_5min.last_rsi, 2), "macd": round(data_5min.last_macd, 4),
                                 "boll": round(data_5min.mid_bollinger, 2)}
                    }
                }
                logger.info(f"✅ {tiker} - КОНФЛЮЕНС НА ПРОДАЖУ (Day, Hour, 5m)")
            # ==========Для телеграмма молния =============


            else:
                logger.debug(
                    f"{tiker} - Конфлюенс не достигнут."
                    f" День:buy={buy_d}/sell={sell_d}-описание {desc_d}=======Данные - {data_day.close}"
                    f" Час:buy={buy_h}/sell={sell_h}-описание {desc_h}=======Данные - {data_hour.close}"
                    f" 5_мин:buy={buy_m}/sell={sell_m}-описание {desc_m}=======Данные - {data_5min.close}")

        except Exception as e:
            logger.error(f"{tiker} - check_confluence() ошибка: {e}")

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
