import os

from dotenv import load_dotenv
from tinkoff.invest import Client, InstrumentStatus


load_dotenv("../terminator/.env.term")  # Если файл в той же папке, что и скрипт
TOKEN = os.getenv("TOKSELL")  # Обратите внимание на имя переменной


def get_all_stock_tickers() -> list[str]:
    """Получает ВСЕ тикеры акций (российские + иностранные)"""
    tickers = []

    with Client(TOKEN) as client:
        # Получаем все акции (базовый статус + все остальные)
        for status in [InstrumentStatus.INSTRUMENT_STATUS_BASE, InstrumentStatus.INSTRUMENT_STATUS_ALL]:
            shares = client.instruments.shares(instrument_status=status)

            for share in shares.instruments:
                # Пропускаем дубликаты
                if share.ticker not in tickers:
                    tickers.append(share.ticker)

    return sorted(tickers)


# Запуск
if __name__ == "__main__":
    all_tickers = get_all_stock_tickers()
    print(f"Найдено {len(all_tickers)} тикеров:\n")
    print(all_tickers)
