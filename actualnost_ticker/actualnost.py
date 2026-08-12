#ПРОВЕРЯЕМ АКТУАЛЬНЫ ЛИ ТИКЕРЫ
from log.logger import inform, logger
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Any
from t_tech.invest import (
    CandleInterval,
    InstrumentIdType,
    InstrumentStatus,
    OperationState,
    OperationType,
    OrderDirection,
    OrderType,
    RequestError,
    Client, # Не забудь импортировать Client
)
from t_tech.invest.services import (
    InstrumentsService,
    StopOrderDirection,
    StopOrderExpirationType,
    StopOrderType,
)


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

    def __init__(self, token: str, file_path: str = "tiker_figi.json",days: int = 7) -> None:
        self.token = token
        self.file_path = file_path    #  это можно не указывать по умолчанию
        self.days = days
        self._client = None  # Клиент создаётся по требованию    зачем это делать

    @property
    def client(self):
        """Ленивое создание клиента."""
        if self._client is None:
            print("подключаю клиента")
            self._client = Client(self.token)
        print("клиент уже есть")
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
                    # save_all_json(cl=cl)
                    return True
                else:
                    inform.info(f"Файл был изменён менее 7 дней. Прошло только {delta.days} дней!!! ВСЕ ОК.")
                    return False
        except Exception as e:
            logger.info(f"last_modified_json() - (ошибка) нет файла tiker_figi.json: Exception as e : {e}")


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
    # def save_all_json(self):
    #     """СОХРАНЯЕТ В JSON "tiker":"figi" """
    #     try:
    #         tikers = list_active_tickers()
    #         for tiker in tikers:
    #             tiker_figi[tiker] = get_figi(tiker=tiker, cl=cl)
    #         with open("tiker_figi.json", "w", encoding="utf-8") as f:
    #             json.dump(tiker_figi, f, indent=4, ensure_ascii=False, sort_keys=True)
    #         return None
    #     except Exception as e:
    #         logger.info(f" - функция save_all_json - не получается сохранить JSON.Exception as e : {e}")
    #         return None
    #
    # def list_active_tickers():
    #     """ПОЛУЧАЕМ СПИСОК ВСЕ АКЦИИ 'на рынке' ИЗ БАЗЫ"""
    #     try:
    #         active_tickers = session.query(AnalysisTiker.tiker).filter(AnalysisTiker.activity == "на рынке").all()
    #         active_tickers = [row[0] for row in active_tickers]
    #         # print(f"СПИСОК АКТИВНЫХ АКЦИЙ {active_tickers}")
    #         return active_tickers
    #     except Exception as e:
    #         logger.info(
    #             f"list_active_tickers() - не получается достать ВСЕ АКЦИИ 'на рынке' ИЗ БАЗЫ Exception as e : {e}")
    # # =================   нужно разобраться почему это все так   =================
    # #  что еще реализовывается в классе что можно сделать

    def __enter__(self):
        print("ентер")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("ексит")
        if self._client is not None:
            self._client.close()  # ← закрываем при выходе из with
            self._client = None






if __name__ == "__main__":
    pass