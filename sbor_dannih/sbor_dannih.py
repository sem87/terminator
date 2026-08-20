import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from t_tech.invest import CandleInterval, Client
from ta.momentum import RSIIndicator  # , MACD
from ta.trend import SMAIndicator  # Раскомментируйте ваши импорты ta
from ta.volatility import BollingerBands

from log.logger import logger


# Загружаем переменные окружения
load_dotenv("../terminator/.env.term")


@dataclass
class IndicatorData:
    """Структура для хранения рассчитанных индикаторов"""

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
    mid_bollinger: float
    volume: float
    mean_volume: float


class SborDannih:
    def __init__(self, session, file_path: str = "tiker_figi.json") -> None:
        self.token = os.getenv("TOKSELL")
        self.file_path = file_path
        self.session = session  # Внедрение зависимости сессии БД
        self.getting_started = time.time()

        # Словари для сигналов
        self.buy_day: dict[str, str] = {}
        self.buy_hour: dict[str, str] = {}
        self.buy_15min: dict[str, str] = {}
        self.sale_day: dict[str, str] = {}
        self.sale_hour: dict[str, str] = {}
        self.sale_15min: dict[str, str] = {}

    def _read_tiker_figi(self) -> dict[str, str]:
        """Заглушка для вашей функции чтения JSON"""
        # Реализуйте чтение self.file_path
        return {}

    def clean_dictionaries(self) -> None:
        """Очищает все словари сигналов перед новым циклом сбора"""
        try:
            self.buy_day.clear()
            self.buy_hour.clear()
            self.buy_15min.clear()
            self.sale_day.clear()
            self.sale_hour.clear()
            self.sale_15min.clear()
        except Exception as e:
            logger.error(f"clean_dictionaries() ошибка: {e}")

    def fetch_candles(self, client: Client, figi: str, days: int, interval: Any, tiker: str) -> pd.DataFrame:
        """Извлекает данные свечей за определенный период"""
        try:
            candle_data = client.market_data.get_candles(
                figi=figi,
                from_=datetime.now() - timedelta(days=days),
                to=datetime.now(),
                interval=interval,
            )
            candles = [
                {
                    "Время": candle.time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Открытие": candle.open.units + candle.open.nano / 1e9,
                    "MAX": candle.high.units + candle.high.nano / 1e9,
                    "MIN": candle.low.units + candle.low.nano / 1e9,
                    "Закрытие": candle.close.units + candle.close.nano / 1e9,
                    "Объем": candle.volume,
                }
                for candle in candle_data.candles
            ]
            return pd.DataFrame(candles)
        except Exception as e:
            logger.warning(f"{tiker} - fetch_candles() ошибка извлечения данных ({interval}, {days} дн.): {e}")
            return pd.DataFrame()

    def calculate_indicators(self, df: pd.DataFrame, tiker: str) -> IndicatorData | None:
        """Рассчитывает технические индикаторы для DataFrame"""
        if df.empty:
            return None

        try:
            df = df.copy()
            df["Время"] = pd.to_datetime(df["Время"])
            df.set_index("Время", inplace=True)

            # SMA 10
            sma_indicator = SMAIndicator(close=df["Закрытие"], window=10)
            df["SMA_10"] = sma_indicator.sma_indicator()

            # RSI 14
            rsi_indicator = RSIIndicator(close=df["Закрытие"], window=14)
            df["RSI"] = rsi_indicator.rsi()

            # # MACD
            # macd_indicator = MACD(close=df["Закрытие"], window_slow=26, window_fast=12, window_sign=9)
            # df["MACD_Hist"] = macd_indicator.macd_diff()

            # Bollinger
            bb_indicator = BollingerBands(close=df["Закрытие"], window=20, window_dev=2)
            df["bb_middle"] = bb_indicator.bollinger_mavg()

            # Извлекаем последние значения
            return IndicatorData(
                last_rsi=float(df["RSI"].iloc[-1]),
                prev_rsi=float(df["RSI"].iloc[-2]),
                prev_rsi_3=float(df["RSI"].iloc[-3]),
                prev_rsi_4=float(df["RSI"].iloc[-4]),
                last_macd=float(df["MACD_Hist"].iloc[-1]),
                prev_macd=float(df["MACD_Hist"].iloc[-2]),
                prev_macd_3=float(df["MACD_Hist"].iloc[-3]),
                prev_macd_4=float(df["MACD_Hist"].iloc[-4]),
                last_sma_10_1=float(df["SMA_10"].iloc[-1]),
                last_sma_10_2=float(df["SMA_10"].iloc[-2]),
                last_sma_10_3=float(df["SMA_10"].iloc[-3]),
                last_sma_10_4=float(df["SMA_10"].iloc[-4]),
                close=float(df["Закрытие"].iloc[-1]),
                mid_bollinger=float(df["bb_middle"].iloc[-1]),
                volume=float(df["Объем"].iloc[-1]),
                mean_volume=float(df["Объем"].iloc[-10:].mean()),
            )
        except Exception as e:
            logger.error(f"{tiker} - calculate_indicators() ошибка расчета: {e}")
            return None

    def evaluate_signals(self, tiker: str, figi: str, interval: Any, indicators: IndicatorData) -> None:
        """Фильтр по спискам на покупку и продажу"""
        try:
            timeframe = (
                "day"
                if interval == CandleInterval.CANDLE_INTERVAL_DAY
                else "hour"
                if interval == CandleInterval.CANDLE_INTERVAL_HOUR
                else "5_min"
            )

            # --- ДНЕВНОЙ ИНТЕРВАЛ ---
            if interval == CandleInterval.CANDLE_INTERVAL_DAY:
                if indicators.last_sma_10_3 < indicators.last_sma_10_2 < indicators.last_sma_10_1:
                    self.buy_day[tiker] = figi
                    self._save_signal(tiker, timeframe, "buy", "1_buy_day) возраст SMA 10", indicators)
                elif indicators.last_sma_10_1 < indicators.last_sma_10_2 < indicators.last_sma_10_3:
                    self.sale_day[tiker] = figi
                    self._save_signal(tiker, timeframe, "sell", "1_sell_day) убывающий SMA 10", indicators)

            # --- ЧАСОВОЙ ИНТЕРВАЛ ---
            elif interval == CandleInterval.CANDLE_INTERVAL_HOUR:
                if (indicators.last_sma_10_3 < indicators.last_sma_10_2 < indicators.last_sma_10_1) and (
                    indicators.prev_rsi < indicators.last_rsi < 65
                ):
                    self.buy_hour[tiker] = figi
                    self._save_signal(tiker, timeframe, "buy", "1_buy_hour) возраст SMA 10, RSI<65", indicators)
                elif (indicators.last_sma_10_1 < indicators.last_sma_10_2 < indicators.last_sma_10_3) and (
                    35 < indicators.last_rsi < indicators.prev_rsi
                ):
                    self.sale_hour[tiker] = figi
                    self._save_signal(tiker, timeframe, "sell", "1_sell_hour) убывающий SMA 10, RSI>35", indicators)

            # --- 5 МИНУТНЫЙ ИНТЕРВАЛ ---
            elif interval == CandleInterval.CANDLE_INTERVAL_5_MIN:
                # Покупка 1
                if (
                    (indicators.close < indicators.mid_bollinger)
                    and (indicators.prev_macd_3 < indicators.prev_macd_4)
                    and (indicators.prev_macd_3 < indicators.prev_macd < indicators.last_macd < 0)
                    and (indicators.prev_rsi < indicators.last_rsi < 50)
                ):
                    self.buy_15min[tiker] = figi
                    self._save_signal(tiker, timeframe, "buy", "1_buy_5_min) нижняя т MACD", indicators)

                # Покупка 2
                elif (
                    (indicators.close < indicators.mid_bollinger)
                    and (indicators.prev_macd_3 < indicators.prev_macd < indicators.last_macd < 0)
                    and (indicators.prev_rsi < indicators.last_rsi < 50)
                ):
                    self.buy_15min[tiker] = figi
                    self._save_signal(tiker, timeframe, "buy", "2_buy_5_min) возраст MACD", indicators)

                # Продажа 1
                elif (
                    (indicators.mid_bollinger < indicators.close)
                    and (indicators.prev_macd_4 < indicators.prev_macd_3)
                    and (0 < indicators.last_macd < indicators.prev_macd < indicators.prev_macd_3)
                    and (50 < indicators.last_rsi < indicators.prev_rsi)
                ):
                    self.sale_15min[tiker] = figi
                    self._save_signal(tiker, timeframe, "sell", "1_sell_5_min) верхняя т. MACD", indicators)

                # Продажа 2
                elif (
                    (indicators.mid_bollinger < indicators.close)
                    and (0 < indicators.last_macd < indicators.prev_macd < indicators.prev_macd_3)
                    and (50 < indicators.last_rsi < indicators.prev_rsi)
                ):
                    self.sale_15min[tiker] = figi
                    self._save_signal(tiker, timeframe, "sell", "2_sell_5_min) убывающий MACD", indicators)

        except Exception as e:
            logger.error(f"{tiker} - evaluate_signals() ошибка: {e}")

    # def _save_signal(self, tiker: str, timeframe: str, action: str, strategy: str, indicators: IndicatorData) -> None:
    #     """Вспомогательный метод для сохранения сигнала в БД"""
    #     filter_tiker = FilterTickerDict(
    #         tiker=tiker,
    #         timeframe=timeframe,
    #         action=action,
    #         strategy=strategy,
    #         description=(
    #             f"last_MACD:{round(indicators.last_macd, 2)}, "
    #             f"last_rsi:{round(indicators.last_rsi, 2)}, "
    #             f"midBoll:{round(indicators.mid_bollinger, 2)}"
    #         ),
    #     )
    #     self.session.add(filter_tiker)
    #     self.session.commit()

    def run(self) -> None:
        """Основной цикл сбора и анализа данных"""
        logger.info("------ НАЧАЛО СБОРА ДАННЫХ -------")
        self.clean_dictionaries()

        tikers = self._read_tiker_figi()
        if not tikers:
            logger.warning("Список тикеров пуст.")
            return

        with Client(self.token) as cl:
            for tiker, figi in tikers.items():
                for interval, days in [
                    (CandleInterval.CANDLE_INTERVAL_DAY, 50),
                    (CandleInterval.CANDLE_INTERVAL_HOUR, 7),
                    (CandleInterval.CANDLE_INTERVAL_5_MIN, 1),
                ]:
                    df = self.fetch_candles(cl, figi, days, interval, tiker)
                    indicators = self.calculate_indicators(df, tiker)

                    if indicators:
                        self.evaluate_signals(tiker, figi, interval, indicators)

        logger.info("------ КОНЕЦ СБОРА ДАННЫХ -------")


if __name__ == "__main__":
    # # Пример использования:
    # # from database import get_session # Ваш импорт сессии
    # session = get_session()
    # analyzer = SborDannih(session=session)
    # analyzer.run()
    pass
