# ПРОВЕРЯЕМ АКТУАЛЬНЫ ЛИ ТИКЕРЫ
from log.logger import inform, logger
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Any
import pandas as pd
from t_tech.invest import (
    CandleInterval,
    InstrumentIdType,
    InstrumentStatus,
    OperationState,
    OperationType,
    OrderDirection,
    OrderType,
    RequestError,
    Client,  # Не забудь импортировать Client
)
from t_tech.invest.services import (
    InstrumentsService,
    StopOrderDirection,
    StopOrderExpirationType,
    StopOrderType,
)
from sql_base.sql_terminator_cuber import AnalysisTiker, session

"""ДЛЯ ЧТЕНИЯ ТОКЕНА"""
load_dotenv("../terminator/.env.term")  # Если файл в той же папке, что и скрипт
token = os.getenv("TOKSELL")  # Обратите внимание на имя переменной
accid = os.getenv("AOCID")  # Обратите внимание на имя переменной
telegtok = os.getenv("TELEGTOKENG")
groupt = os.getenv("GROUPT")
api_iddd = os.getenv("API_IDDD")
proxy_url = os.getenv("PROXY_URL")


class ActualniiTiker:
    """Работа с актуальными тикерами и их FIGI."""

    def __init__(self, token: str, file_path: str = "tiker_figi.json", days: int = 7) -> None:
        self.token = token
        self.file_path = file_path
        self.days = days
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

    def last_modified_json(self):
        """ПРОВЕРЯЕТ ДАВНО ЛИ ОБНОВЛЯЛСЯ tiker_figi.json"""
        try:
            # Получаем время последнего изменения файла (в секундах с эпохи)
            if os.path.exists(self.file_path):
                last_modified = os.path.getmtime(self.file_path)
                # Разница во времени
                delta = datetime.now() - datetime.fromtimestamp(last_modified)
                if delta >= timedelta(days=self.days):
                    inform.info(f"Обновляем ФИГИ в tiker_figi.json. Прошло {delta.days} дней!!!")
                    self.save_all_json()
                    return True
                else:
                    inform.info(f"Файл был изменён менее {self.days} дней. Прошло только {delta.days} дней!!! ВСЕ ОК.")
                    return False
        except Exception as e:
            logger.info(
                f"ActualniiTiker last_modified_json() - (ошибка) нет файла tiker_figi.json: Exception as e : {e}")

    # ---------НАЧАЛО ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ----------------
    def save_all_json(self):
        """СОХРАНЯЕТ В JSON "tiker":"figi" """
        try:
            tikers = self.list_active_tickers()
            for tiker in tikers:
                self.tiker_figi[tiker] = self.get_figi(tiker=tiker)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.tiker_figi, f, indent=4, ensure_ascii=False, sort_keys=True)
            return True
        except Exception as e:
            logger.info(f"ActualniiTiker save_all_json - не получается сохранить JSON.Exception as e : {e}")
            return False

    def _load_all_instruments(self):
        """ЗАГРУЖАЕТ ВСЕ ТИПЫ ИНСТРУМЕНТОВ И КЭШИРУЕТ ИХ"""
        if hasattr(self, '_all_instruments_df'):
            return  # Уже загружено, не грузим повторно
        instruments: InstrumentsService = self.client.instruments
        all_data = []
        # Все доступные типы инструментов
        methods = {
            'shares': 'Акции',
            'bonds': 'Облигации (ОФЗ)',
            'etfs': 'ETF',
            'currencies': 'Валюты (золото)',
            'futures': 'Фьючерсы',
        }
        for method_name, type_name in methods.items():
            try:
                # Динамически вызываем нужный метод API
                method = getattr(instruments, method_name)
                result = method(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE)
                # Превращаем в DataFrame
                df = pd.DataFrame(
                    result.instruments,
                    columns=["name", "figi", "ticker", "class_code"]
                )
                df['type'] = type_name
                all_data.append(df)
                logger.info(f"Загружено {type_name}: {len(df)} шт.")
            except Exception as e:
                logger.info(f"Ошибка загрузки {type_name}: {e}")
        # Склеиваем все инструменты в один общий DataFrame
        self._all_instruments_df = pd.concat(all_data, ignore_index=True)

    def get_figi(self, tiker: str) -> str | None:
        """УНИВЕРСАЛЬНЫЙ ПОИСК FIGI ДЛЯ ЛЮБОГО ТИКЕРА"""
        # instruments.shares()-Акции
        # instruments.bonds()-Облигации(включая ОФЗ)
        # instruments.etfs()-ETF(фонды)
        # instruments.currencies()-Валюты(включая-золото — торгуется-как-валютная-пара-GLD_RUB)
        # instruments.futures()-Фьючерсы
        # instruments.options()-Опционы
        # Загружаем все инструменты (кешируется после первого вызова)
        self._load_all_instruments()
        # Ищем тикер во всех типах инструментов сразу
        mask = self._all_instruments_df["ticker"] == tiker
        matches = self._all_instruments_df[mask]
        # Не найден
        if matches.empty:
            logger.info(f"Тикер '{tiker}' не найден ни в одном типе инструментов")
            return None
        # Найден в нескольких (бывает для разных бирж)
        if len(matches) > 1:
            logger.info(
                f"Тикер '{tiker}' найден в нескольких инструментах:\n"
                f"{matches[['ticker', 'type', 'name', 'class_code']].to_string(index=False)}\n"
                f"Берём первый: {matches.iloc[0]['name']} ({matches.iloc[0]['type']})"
            )
        return matches["figi"].iloc[0]

    def read_tiker_figi_json(self) -> dict[str, Any]:
        """Читает данные из JSON."""
        try:
            with open(self.file_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.info(f"Повреждён JSON: {e}")
        except OSError as e:
            logger.info(f"Ошибка чтения: {e}")
        return {}

    def list_active_tickers(self):
        """ПОЛУЧАЕМ СПИСОК ВСЕ АКЦИИ 'на рынке' ИЗ БАЗЫ"""
        try:
            active_tickers = session.query(AnalysisTiker.tiker).filter(AnalysisTiker.activity == "на рынке").all()
            active_tickers = [row[0] for row in active_tickers]
            logger.info(f"СПИСОК АКТИВНЫХ АКЦИЙ {active_tickers}")
            return active_tickers
        except Exception as e:
            logger.info(
                f"ActualniiTiker list_active_tickers() - не получается достать ВСЕ АКЦИИ 'на рынке' ИЗ БАЗЫ Exception as e : {e}")

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
        return f"Срабатывает класс с количеством дней {self.days}"

    # ---------КОНЕЦ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ----------------


if __name__ == "__main__":
    pass
