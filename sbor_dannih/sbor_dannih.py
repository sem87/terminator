from log.logger import inform
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
from dotenv import load_dotenv
import os



# Загружаем переменные окружения один раз при импорте
load_dotenv("../terminator/.env.term")





class SborDannih:
    def __init__(self, file_path: str = "tiker_figi.json", days: int = 7) -> None:
        self.token = os.getenv("TOKSELL")
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
        return f"Это сбор данных"



if __name__ == "__main__":
    pass