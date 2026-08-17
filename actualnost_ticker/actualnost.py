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
        self.file_path = file_path  # это можно не указывать по умолчанию
        self.days = days
        self._client = None  # Клиент создаётся по требованию    зачем это делать
        self.tiker_figi = {}

    @property
    def client(self):
        """ЛЕНИВОЕ СОЗДАНИЕ КЛИЕНТА"""
        if self._client is None:
            self._client = Client(self.token)
        return self._client

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
            logger.info(f"last_modified_json() - (ошибка) нет файла tiker_figi.json: Exception as e : {e}")

    # ---------НАЧАЛО ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ----------------
    def save_all_json(self):
        """СОХРАНЯЕТ В JSON "tiker":"figi" """
        try:
            tikers = self.list_active_tickers()
            for tiker in tikers:
                self.tiker_figi[tiker] = self.get_figi(tiker=tiker, cl=self.client)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.tiker_figi,f, indent=4, ensure_ascii=False, sort_keys=True)
            return None
        except Exception as e:
            logger.info(f" - функция save_all_json - не получается сохранить JSON.Exception as e : {e}")
            return None


    def get_figi(self, cl, tiker: str):
        """ИЗВЛЕКАЕТ ИЗ ТИКЕРА ФИГИ"""
        try:
            instruments: InstrumentsService = cl.instruments
            # market_data: MarketDataService = cl.market_data
            # Забирает данные для INSTRUMENT_STATUS_BASE
            df = pd.DataFrame(
                instruments.shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments,
                columns=["name", "figi", "ticker", "class_code"],
            )
            # for method in ['shares' АКЦИИ, 'bonds', 'etfs' ]:
            # 'currencies', 'futures']:  ОБЛИГАЦИИ ЕТФ ОПЦИОНЫ НУЖНО РАЗБИРАТЬСЯ
            figi = df[df["ticker"] == tiker]["figi"].iloc[0]
            return figi
        except Exception as e:
            logger.info(f" {tiker} - функция get_figi() - не получается достать figi Exception as e : {e}")
            return None


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

    # # =================   нужно разобраться почему это все так   =================

    def list_active_tickers(self):
        """ПОЛУЧАЕМ СПИСОК ВСЕ АКЦИИ 'на рынке' ИЗ БАЗЫ"""
        try:
            active_tickers = session.query(AnalysisTiker.tiker).filter(AnalysisTiker.activity == "на рынке").all()
            active_tickers = [row[0] for row in active_tickers]
            print(f"СПИСОК АКТИВНЫХ АКЦИЙ {active_tickers}")
            return active_tickers
        except Exception as e:
            logger.info(
                f"list_active_tickers() - не получается достать ВСЕ АКЦИИ 'на рынке' ИЗ БАЗЫ Exception as e : {e}")

    # =================   нужно разобраться почему это все так   =================
    #  что еще реализовывается в классе что можно сделать

    # ---------КОНЕЦ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ----------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client is not None:
            self._client.close()  # ← закрываем при выходе из with
            self._client = None

    def __str__(self):
        return f"Срабатывает класс с количеством дней {self.days}"


if __name__ == "__main__":
    pass
