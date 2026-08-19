import os
import time

from dotenv import load_dotenv
from t_tech.invest import (
    Client,  # Не забудь импортировать Client
)

from log.logger import logger


# Загружаем переменные окружения один раз при импорте
load_dotenv("../terminator/.env.term")


class SborDannih:
    def __init__(self, file_path: str = "tiker_figi.json") -> None:
        self.token = os.getenv("TOKSELL")
        self.file_path = file_path
        self.getting_started = time.time()
        self._client = None  # Сам канал
        self._services = None  # Объект Services с методами API (instruments, orders и т.д.)
        self.tiker_figi = {}

    @property
    def client(self):
        """ЛЕНИВОЕ СОЗДАНИЕ КЛИЕНТА И ПОЛУЧЕНИЕ SERVICES"""
        if self._services is None:
            self._client = Client(self.token)
            # __enter__ открывает канал и возвращает объект Services
            self._services = self._client.__enter__()
        return self._services

    def cleaning_dict(self, new_dict: dict):
        """ОЧИЩАЕТ ВСЕ СЛОВАРИ ПЕРЕД СБОРОМ ДАННЫХ"""
        # из за того что цикл их нужно очищать
        try:
            new_dict.clear()
            return new_dict
        except Exception as e:
            logger.info(f"cleaning_dict() ошибка очистка словарей : Exception as e : {e}")

    # def candl(cl, day: int, interval, figi: str, tiker: str) -> pd.DataFrame:
    #     """ИЗВЛЕКАЕТ ДАННЫЕ ИЗ СВЕЧЕК ЗА ОПРЕДЕЛЕННЫЙ ПЕРИОД"""
    #     try:
    #         # Получаем данные о свечах указываем интервал
    #         candle_data = cl.market_data.get_candles(
    #             figi=figi,
    #             from_=now() - timedelta(days=day),  # было day=1 (неверно)
    #             to=now(),  # было datetime.UTC() (неверно)
    #             interval=interval,
    #         )  # '''CandleInterval.CANDLE_INTERVAL_15_MIN  # нужно указать конкретный интервал'''
    #         # Преобразуем в удобный формат
    #         candles = []
    #         for candle in candle_data.candles:
    #             candles.append(
    #                 {
    #                     "Время": candle.time.strftime("%Y-%m-%d %H:%M:%S"),
    #                     "Открытие": candle.open.units + candle.open.nano / 1e9,
    #                     "МАХ": candle.high.units + candle.high.nano / 1e9,
    #                     "MIN": candle.low.units + candle.low.nano / 1e9,
    #                     "Закрытие": candle.close.units + candle.close.nano / 1e9,
    #                     "Объем": candle.volume,
    #                 }
    #             )
    #         # Создаем DataFrame для красивого отображения
    #         df = pd.DataFrame(candles)
    #         return df
    #     except Exception as e:
    #         logger.info(f"{tiker} - candl() извлечение данных : {interval},период : {day} , Exception as e : {e}")
    #         df = pd.DataFrame(None)
    #         # Проверить когда пустой Дата фрейм???
    #         return df
    #
    # def calculate_indicator(df: pd.DataFrame, tiker: str) -> tuple:
    #     """Рассчитывает технические индикаторы для DataFrame"""
    #     """СМЫСЛ В ТОМ ЧТОБЫ УСТАНОВИТЬ ВОСХОДЯЩИЙ ЛИ ТРЕНД"""
    #     try:
    #         # Преобразуем время в datetime и устанавливаем как индекс
    #         df["Время"] = pd.to_datetime(df["Время"])
    #         df.set_index("Время", inplace=True)
    #         "SMA 10"
    #         # Рассчитываем SMA с периодом 10 предел в 45 почему-то
    #         sma_indicator = SMAIndicator(close=df["Закрытие"], window=10)
    #         df["SMA_10"] = sma_indicator.sma_indicator()
    #         # Получаем последние значения
    #         last_sma_10_1 = df["SMA_10"].iloc[-1]
    #         last_sma_10_2 = df["SMA_10"].iloc[-2]
    #         last_sma_10_3 = df["SMA_10"].iloc[-3]
    #         last_sma_10_4 = df["SMA_10"].iloc[-4]
    #         "КОНЕЦ SMA 10"
    #         """НАЧАЛО RSI"""
    #         # Рассчитываем RSI (период 14 по умолчанию)
    #         rsi_indicator = RSIIndicator(close=df["Закрытие"], window=14)
    #         df["RSI"] = rsi_indicator.rsi()
    #         last_rsi = df["RSI"].iloc[-1]  # Последнее значение
    #         prev_rsi = df["RSI"].iloc[-2]  # Предпоследнее значение
    #         prev_rsi_3 = df["RSI"].iloc[-3]
    #         prev_rsi_4 = df["RSI"].iloc[-4]
    #         """КОНЕЦ RSI"""
    #         """НАЧАЛО MACD"""
    #         # Рассчитываем MACD
    #         macd_indicator = MACD(close=df["Закрытие"], window_slow=26, window_fast=12, window_sign=9)
    #         df["MACD"] = macd_indicator.macd()  # Линия MACD (разница 12 и 26 EMA)
    #         df["MACD_Signal"] = macd_indicator.macd_signal()  # Сигнальная линия (EMA от MACD)
    #         df["MACD_Hist"] = macd_indicator.macd_diff()  # Гистограмма (MACD - Signal)
    #         last_macd = df["MACD_Hist"].iloc[-1]
    #         prev_macd = df["MACD_Hist"].iloc[-2]
    #         prev_macd_3 = df["MACD_Hist"].iloc[-3]
    #         prev_macd_4 = df["MACD_Hist"].iloc[-4]
    #         """КОНЕЦ MACD"""
    #         """НАЧАЛО Bollinger"""
    #         # Инициализация индикатора Bollinger Bands
    #         indicator_bb = BollingerBands(close=df["Закрытие"], window=20, window_dev=2)
    #         # Добавление полос Боллинджера в DataFrame
    #         # df['bb_upper'] = indicator_bb.bollinger_hband()  # Верхняя полоса
    #         df["bb_middle"] = indicator_bb.bollinger_mavg()  # Средняя линия (SMA)
    #         # df['bb_lower'] = indicator_bb.bollinger_lband()  # Нижняя полоса
    #         midle_bollinger = df["bb_middle"].iloc[-1]  # Средняя линия Боллинджера
    #         """КОНЕЦ Bollinger"""
    #         close = df["Закрытие"].iloc[-1]  # Цена закрытия
    #         """ДОСТАЕМ ОБЪЕМ"""
    #         volume = df["Объем"].iloc[-1]  # Объем последний
    #         mean_volume = df["Объем"].iloc[-10:].mean()
    #         """КОНЕЦ ОБЪЕМ"""
    #         return (
    #             last_rsi,
    #             prev_rsi,
    #             prev_rsi_3,
    #             prev_rsi_4,
    #             last_macd,
    #             prev_macd,
    #             prev_macd_3,
    #             prev_macd_4,
    #             last_sma_10_1,
    #             last_sma_10_2,
    #             last_sma_10_3,
    #             last_sma_10_4,
    #             close,
    #             midle_bollinger,
    #             volume,
    #             mean_volume,
    #         )  # Возвращаем последние и предпоследние значения
    #     except Exception as e:
    #         logger.info(f"{tiker} - calculate_indicator() расчет тех индикатора : Exception as e : {e}")
    #         return ()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ПРАВИЛЬНОЕ ЗАКРЫТИЕ КАНАЛА"""
        if self._client is not None:
            # Закрываем gRPC-канал через __exit__
            self._client.__exit__(exc_type, exc_val, exc_tb)
            self._client = None
            self._services = None

    def __str__(self):
        return "Это сбор данных"


if __name__ == "__main__":
    pass
