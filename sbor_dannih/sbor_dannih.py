import os
from dataclasses import dataclass
from datetime import timedelta

import pandas as pd
from dotenv import load_dotenv
from t_tech.invest import CandleInterval, Client
from t_tech.invest.utils import now
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands

from log.logicuber import system_log, trade_log

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
    mid_bollinger: float
    volume: float
    mean_volume: float


class SborDannih:
    """КЛАСС СОБИРАЕТ ДАННЫЕ"""

    def __init__(self) -> None:
        self.token = os.getenv("TOKSELL")
        self._client = None  # Сам канал
        self._services = None  # Объект Services с методами API (instruments, orders и т.д.)
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
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ПРАВИЛЬНОЕ ЗАКРЫТИЕ КАНАЛА"""
        if self._client is not None:
            self._client.__exit__(exc_type, exc_val, exc_tb)
            self._client = None
            self._services = None

    def cleaning_dict(self):
        self.buy_itog.clear()
        self.sale_itog.clear()
        self.buy_itog_d_h.clear()
        self.sale_itog_d_h.clear()

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
            system_log.critical(
                f"{tiker} - SborDannih в candl() извлечение данных : {interval},период : {day} , Exception as e : {e}"
            )
            df = pd.DataFrame(None)
            # Проверить когда пустой Дата фрейм???
            system_log.critical(
                f"{tiker} - SborDannih в candl() - нужно что-то придумать с пустым дата фреймом,проверить с какими именно тикерами"
            )
            return df

    def calculate_indicator(self, df: pd.DataFrame, tiker: str) -> IndicatorData | None:
        """Рассчитывает технические индикаторы для DataFrame"""
        try:
            # 1. Безопасная копия
            work_df = df.copy()
            work_df["Время"] = pd.to_datetime(work_df["Время"])
            work_df.set_index("Время", inplace=True)
            # 2. Расчет индикаторов (библиотека ta)
            work_df["SMA_10"] = SMAIndicator(close=work_df["Закрытие"], window=10).sma_indicator()
            work_df["RSI"] = RSIIndicator(close=work_df["Закрытие"], window=14).rsi()
            work_df["MACD_Hist"] = MACD(
                close=work_df["Закрытие"], window_slow=26, window_fast=12, window_sign=9
            ).macd_diff()
            work_df["bb_middle"] = BollingerBands(close=work_df["Закрытие"], window=20, window_dev=2).bollinger_mavg()
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
            system_log.error(
                f"{tiker} - SborDannih в calculate_indicator() (может следствие пустого дата фрейма)ошибка: {e}"
            )
            return None

    # ==================НАЧАЛО ФИЛЬТР СТРАТЕГИЙ (ОЦЕНКА ТАЙМФРЕЙМА)===============
    def _filtr_ozenki_strategy_day_hour_5min(self, tf_name: str, data: IndicatorData) -> tuple[bool, bool, str]:
        """Оценивает сигналы для одного таймфрейма. Возвращает (is_buy, is_sell, description)"""
        # НУЖНО СДЕЛАТЬ SCORE И ФИЛЬТРАЦИЮ  !!!!!!!!!!!!!!!!!
        # фильтр SMA (подготовка)
        sma_up = data.last_sma_10_3 < data.last_sma_10_2 < data.last_sma_10_1
        sma_down = data.last_sma_10_1 < data.last_sma_10_2 < data.last_sma_10_3
        # фильтр боллинджер
        close_below_boll = data.close < data.mid_bollinger
        close_above_boll = data.close > data.mid_bollinger

        is_buy, is_sell = False, False
        desc = ""
        # Сделать подробное описание стратегий и так что-бы не запутаться
        if tf_name == "day":
            if sma_up:
                is_buy, desc = True, "SMA10 вверх"
            elif sma_down:
                is_sell, desc = True, "SMA10 вниз"

        elif tf_name == "hour":
            if sma_up and (data.prev_rsi < data.last_rsi < 65):
                is_buy, desc = True, "SMA10 вверх,RSI<65"
            elif sma_down and (35 < data.last_rsi < data.prev_rsi):
                is_sell, desc = True, "SMA10 вниз,RSI>35"

        elif tf_name == "5_min":
            # ==========Покупка: описания отражают суть паттерна...перебирает пары ключ-значение в том порядке, в котором они записаны...
            # next() мгновенно возвращает соответствующий ключ (desc) и прекращает дальнейший перебор
            buy_conds = {
                "Цена<Боллинджера;MACD разворот вверх из -;RSI<50": close_below_boll
                                                                    and data.prev_macd_3 < data.prev_macd_4
                                                                    and data.prev_macd_3 < data.prev_macd < data.last_macd < 0
                                                                    and data.prev_rsi < data.last_rsi < 50,
                "Цена<Боллинджера;MACD рост из -;RSI<50": close_below_boll
                                                          and data.prev_macd_3 < data.prev_macd < data.last_macd < 0
                                                          and data.prev_rsi < data.last_rsi < 50,
                "Цена<Боллинджера;Тренд SMA вверх;RSI<55": close_below_boll
                                                           and sma_up
                                                           and data.prev_rsi < data.last_rsi < 55,
                "Тренд SMA вверх;RSI<50": sma_up and data.prev_rsi < data.last_rsi < 50,
                "Цена<Боллинджера;MACD отскок от дна;RSI<50": close_below_boll
                                                              and data.prev_macd < data.prev_macd_3
                                                              and data.prev_macd < data.last_macd < 0
                                                              and data.prev_rsi < data.last_rsi < 50,
            }
            triggered_desc_buy_5min = next((desc for desc, cond in buy_conds.items() if cond), None)
            # debug_log.info(f"5мин для проверки {triggered_desc_buy_5min}")
            if triggered_desc_buy_5min:
                is_buy = True
                desc = f"BUY: {triggered_desc_buy_5min}"

            # ==========Продажа: описания отражают суть паттерна
            sell_conds = {
                "Цена > BB + MACD разворот вниз из + + RSI>50": close_above_boll
                                                                and data.prev_macd_4 < data.prev_macd_3
                                                                and 0 < data.last_macd < data.prev_macd < data.prev_macd_3
                                                                and 50 < data.last_rsi < data.prev_rsi,
                "Цена > BB + MACD снижение из + + RSI>50": close_above_boll
                                                           and 0 < data.last_macd < data.prev_macd < data.prev_macd_3
                                                           and 50 < data.last_rsi < data.prev_rsi,
                "Цена > BB + Тренд SMA вниз + RSI снижение": close_above_boll
                                                             and sma_down
                                                             and 45 < data.last_rsi < data.prev_rsi,
                "Тренд SMA вниз + RSI>50 снижение": sma_down and 50 < data.last_rsi < data.prev_rsi,
                "Цена > BB + MACD снижение от пика + RSI>50": close_above_boll
                                                              and data.prev_macd_3 < data.prev_macd
                                                              and 0 < data.last_macd < data.prev_macd
                                                              and 50 < data.last_rsi < data.prev_rsi,
            }
            triggered_desc_sell_5min = next((desc for desc, cond in sell_conds.items() if cond), None)
            if triggered_desc_sell_5min:
                is_sell = True
                desc = f"SELL: {triggered_desc_sell_5min}"
        return is_buy, is_sell, desc

    def _filtr_ozenki_strategy_telega_day_hour(self, tf_name: str, data: IndicatorData) -> tuple[
        bool, bool, float, str]:
        """Оценивает сигналы для одного таймфрейма. Возвращает (is_buy, is_sell, score, description)"""
        # фильтр SMA
        sma_up = data.last_sma_10_3 < data.last_sma_10_2 < data.last_sma_10_1
        sma_down = data.last_sma_10_1 < data.last_sma_10_2 < data.last_sma_10_3
        # фильтр MACD
        macd_up = data.last_macd > data.prev_macd_3
        macd_down = data.last_macd < data.prev_macd_3
        # фильтр RSI
        rsi_up = data.last_rsi > data.prev_rsi_3
        rsi_down = data.last_rsi < data.prev_rsi_3
        # фильтр объёма
        v, m = data.volume, data.mean_volume
        vol_txt, vol_score = ("высокий", 1.0) if v > 2 * m else ("выше средн", 0.5) if v > m else (
            "средн", 0.0) if v >= .5 * m else ("низкий", -1.0)
        # текстовые описания индикаторов
        macd_txt = f"MACD{'↑' if macd_up else ('↓' if macd_down else '→')}{'>0' if data.last_macd > 0 else '<0'}"
        vol_block = f"Обьем:{vol_txt}({v / m:.2f})"
        rsi_block = f"RSI{'↑' if rsi_up else ('↓' if rsi_down else '→')}={data.last_rsi:.1f}"
        # === Расчёт score ===
        ydelnii_ves = {'sma': 0.25, 'rsi_d': 0.15, 'macd_s': 0.20, 'macd_d': 0.15, 'vol': 0.25}
        score = 0.0
        score += ydelnii_ves['sma'] * (1 if sma_up else (-1 if sma_down else 0))
        score += ydelnii_ves['rsi_d'] * (1 if rsi_up else (-1 if rsi_down else 0))
        score += ydelnii_ves['macd_s'] * (1 if data.last_macd > 0 else -1)
        score += ydelnii_ves['macd_d'] * (1 if macd_up else (-1 if macd_down else 0))
        score += ydelnii_ves['vol'] * vol_score
        is_buy, is_sell = False, False
        desc = ""
        if tf_name == "day":
            if sma_up:
                is_buy = True
                desc = f"SMA10↑; {rsi_block}; {macd_txt}; {vol_block}"
            elif sma_down:
                is_sell = True
                desc = f"SMA10↓; {rsi_block}; {macd_txt}; {vol_block}"
        elif tf_name == "hour":
            if sma_up and (rsi_up < 65):
                is_buy = True
                desc = f"SMA10↑; {rsi_block}; {macd_txt}; {vol_block}"
            elif sma_down and (35 < rsi_down):
                is_sell = True
                desc = f"SMA10↓; {rsi_block}; {macd_txt}; {vol_block}"
        return is_buy, is_sell, score, desc

    # ==================КОНЕЦ ФИЛЬТР СТРАТЕГИЙ (ОЦЕНКА ТАЙМФРЕЙМА)===============
    # ==================НАЧАЛО СТРАТЕГИЙ ================
    def strategy_day_hour_5min(
            self, figi: str, tiker: str, data_day: IndicatorData, data_hour: IndicatorData, data_5min: IndicatorData
    ):
        """СТРАТЕГИЯ проверяет одновременное выполнение условий на Day, Hour и 5min"""
        try:
            # 1. Оцениваем каждый таймфрейм отдельно
            buy_d, sell_d, desc_d = self._filtr_ozenki_strategy_day_hour_5min("day", data_day)
            buy_h, sell_h, desc_h = self._filtr_ozenki_strategy_day_hour_5min("hour", data_hour)
            buy_m, sell_m, desc_m = self._filtr_ozenki_strategy_day_hour_5min("5_min", data_5min)

            # 2. Проверяем строгий конфлюенс (все 3 должны быть True)
            if buy_d and buy_h and buy_m:
                self.buy_itog[tiker] = {
                    "figi": figi,
                    "action": "buy",
                    "strategy": "ДЕНЬ+ЧАС+5МИН",
                    "description": f"ДЕНЬ:{desc_d}***ЧАС:{desc_h}***5МИН: {desc_m}",
                    "indicators": {
                        "day": {"rsi": round(data_day.last_rsi, 2), "sma": round(data_day.last_sma_10_1, 2)},
                        "hour": {"rsi": round(data_hour.last_rsi, 2), "sma": round(data_hour.last_sma_10_1, 2)},
                        "5min": {
                            "rsi": round(data_5min.last_rsi, 2),
                            "macd": round(data_5min.last_macd, 3),
                            "boll": round(data_5min.mid_bollinger, 2),
                        },
                    },
                }
                trade_log.debug(f"{tiker}-ПОКУПКА strategy_day_hour_5min")
            elif sell_d and sell_h and sell_m:
                self.sale_itog[tiker] = {
                    "figi": figi,
                    "action": "sell",
                    "strategy": "ДЕНЬ+ЧАС+5МИН",
                    "description": f"ДЕНЬ:{desc_d}***ЧАС:{desc_h}***5МИН: {desc_m}",
                    "indicators": {
                        "day": {"rsi": round(data_day.last_rsi, 2), "sma": round(data_day.last_sma_10_1, 2)},
                        "hour": {"rsi": round(data_hour.last_rsi, 2), "sma": round(data_hour.last_sma_10_1, 2)},
                        "5min": {
                            "rsi": round(data_5min.last_rsi, 2),
                            "macd": round(data_5min.last_macd, 3),
                            "boll": round(data_5min.mid_bollinger, 2),
                        },
                    },
                }
                trade_log.info(f"{tiker}-ПРОДАЖА strategy_day_hour_5min")
            else:
                pass
                # trade_log.critical(f"{tiker} - НЕ ПОДХОДИТ К УСЛОВИЯМ СТРАТЕГИИ strategy_day_hour_5min()")
        except Exception as e:
            system_log.error(f"{tiker} - SborDannih check_confluence() ошибка: {e}")

    def strategy_telega_day_hour(self, figi: str, tiker: str, data_day: IndicatorData, data_hour: IndicatorData):
        """Стратегия телеграм условие для Day, Hour"""
        try:
            # 1. Оцениваем каждый таймфрейм отдельно
            buy_d, sell_d, score_d, desc_d = self._filtr_ozenki_strategy_telega_day_hour("day", data_day)
            buy_h, sell_h, score_h, desc_h = self._filtr_ozenki_strategy_telega_day_hour("hour", data_hour)
            # 2. Проверяем строгий конфлюенс (все день и час должны быть True)
            # ==========Для телеграмма молния =============
            if buy_d and buy_h:
                self.buy_itog_d_h[tiker] = {
                    "figi": figi,
                    "action": "buy",
                    "strategy": "ТЕЛЕГА ДЕНЬ↑+ЧАС(↑+rsi_up<65)",
                    "score_hour": score_h,
                    "score": f"счет Д📅{score_d:+.2f},Ч⏱️{score_h:+.2f},ИТОГ🎯{score_d * 0.6 + score_h * 0.4:+.2f}",
                    "description": f"<b>ДЕНЬ</b>:{desc_d}\n<b>ЧАС</b>:{desc_h}",
                    "indicators": {
                        "day": {"rsi": round(data_day.last_rsi, 2), "sma": round(data_day.last_sma_10_1, 2)},
                        "hour": {
                            "sma": round(data_hour.last_sma_10_1, 2),
                            "rsi": round(data_hour.last_rsi, 2),
                            "macd": round(data_hour.last_macd, 2),
                            "vol_mean": round(data_hour.mean_volume, 2),
                            "vol": round(data_hour.volume, 2)
                        },
                    },
                }
                trade_log.info(f"{tiker}-ТЕЛЕГА покупка strategy_telega_day_hour")
            elif sell_d and sell_h:
                self.sale_itog_d_h[tiker] = {
                    "figi": figi,
                    "action": "sell",
                    "strategy": "ТЕЛЕГА ДЕНЬ↓+ЧАС(↓+35<rsi_down)",
                    "score_hour": score_h,
                    "score": f"счет Д📅{score_d:+.2f},Ч⏱️{score_h:+.2f},ИТОГ🎯{score_d * 0.6 + score_h * 0.4:+.2f}",
                    "description": f"<b>ДЕНЬ</b>:{desc_d}\n<b>ЧАС</b>:{desc_h}",
                    "indicators": {
                        "day": {"rsi": round(data_day.last_rsi, 2), "sma": round(data_day.last_sma_10_1, 2)},
                        "hour": {
                            "sma": round(data_hour.last_sma_10_1, 2)},
                            "rsi": round(data_hour.last_rsi, 2),
                            "macd": round(data_hour.last_macd, 2),
                            "vol_mean": round(data_hour.mean_volume, 2),
                            "vol": round(data_hour.volume, 2)
                    },
                }
                trade_log.info(f"{tiker}-ТЕЛЕГА продажа strategy_telega_day_hour")
            # ==========Для телеграмма молния =============
            else:
                pass
        except Exception as e:
            system_log.error(f"{tiker} - SborDannih strategy_telega_day_hour ошибка: {e}")

    # ==================КОНЕЦ СТРАТЕГИЙ =================

    @property
    def client(self):
        """ЛЕНИВОЕ СОЗДАНИЕ КЛИЕНТА И ПОЛУЧЕНИЕ SERVICES"""
        if self._services is None:
            self._client = Client(self.token)
            # __enter__ открывает канал и возвращает объект Services
            self._services = self._client.__enter__()
        return self._services

    def __str__(self):
        return "ЭТО КЛАСС СБОР ДАННЫХ"


class PrivlicatelnostChitaemost:
    def __init__(self, signals: dict, sort_by_score_hour: bool = True, reverse: bool = False):
        """signals: словарь тикеров   sort_by_hour_rsi: если True — сортируем по RSI hour в конструкторе
        reverse True - по убыванию RSI"""
        if sort_by_score_hour:
            self.signals = dict(
                sorted(
                    signals.items(),
                    key=lambda item: item[1]["score_hour"],
                    reverse=reverse,
                )
            )
        else:
            self.signals = signals

    def format_signals_to_tuple(self) -> str:
        """Формирует текст из уже отсортированных сигналов."""
        lines = [f"{len(self.signals)} шт\n"]
        for ticker, data in self.signals.items():
            # d = data["indicators"]["day"]
            # h = data["indicators"]["hour"]
            lines.append(f"👉 <b>{ticker}</b>\n{data['score']}\n{data['description']}\nСОПУТСТВУЮЩИЕ СДЕСЬ\n")
            # f"Д:RSI:{d['rsi']:.1f}\n"
            # f"Ч:RSI:{h['rsi']:.1f}\n"
        text = "\n".join(lines)
        if len(text) > 4090:
            text = text[:4077] + "ЛИМИТ ТЕЛЕГИ"
        return text


if __name__ == "__main__":
    pass
