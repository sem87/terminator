from utils import *


def get_figi(cl, tiker: str):
    """ИЗВЛЕКАЕТ ИЗ ТИКЕРА ФИГИ"""
    try:
        instruments: InstrumentsService = cl.instruments
        # market_data: MarketDataService = cl.market_data
        # Забирает данные для INSTRUMENT_STATUS_BASE
        df = pd.DataFrame(instruments.shares(
            instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments,
                          columns=["name", "figi", "ticker", "class_code"])
        # for method in ['shares' АКЦИИ, 'bonds', 'etfs' ]:
        # 'currencies', 'futures']:  ОБЛИГАЦИИ ЕТФ ОПЦИОНЫ НУЖНО РАЗБИРАТЬСЯ
        figi = df[df["ticker"] == tiker]["figi"].iloc[0]
        return figi
    except Exception as e:
        logger.info(f" {tiker} - функция get_figi() - не получается достать figi Exception as e : {e}")
        return None


if __name__ == "__main__":
    with Client(token) as cl:
        save_all_json(cl=cl)
