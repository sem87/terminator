from utils import *

tiker_figi = {}
# Полный список
# tikers = [
#     "SBER", "ROSN", "LKOH", "ZAYM", "SNGS", "TATN", "BANE", "ELFV", "SLAV", "YAKG", "RNFT", "SIBN", "TGKN", "NVTK",
#     "GAZP", "MOEX", "MBNK", "BSPB", "SPBE", "ZAYM", "RENI", "VTBR", "SVCB", "CBOM", "MGKL", "CARM", "MGNT", "GCHE",
#     "KROT", "LENT", "SVAV", "AQUA", "HNFG", "BELU", "ABRD", "OKEY", "NKHP", "GTRK", "WUSH", "MSTT", "EUTR", "KMAZ",
#     "FLOT", "FESH", "UWGN", "NMTP", "ABIO", "HEAD", "ASTR", "DELI", "LEAS", "KZIZ", "SMLT", "LSRG", "PIKK", "TGKJ",
#     "VSMO", "PLZL", "AKRN", "LNZL", "CHMK", "PHOR", "CHMF", "KAZT", "ENPG", "NLMK", "GMKN", "NKNC", "KZOS", "MRKZ",
#     "ALRS", "RUAL", "PRFN", "UGLD", "NSVZ", "RTKM", "CNTL", "TTLK", "VRSB", "PMSB", "KLSB", "LSNG", "IRAO", "DVEC",
#     "UPRO", "MSRS", "MRKC", "MRKP", "MRKV", "MRKY", "T"]
# Чем торгую
tikers = ["SBER", "ROSN", "SNGS", "TATN", "RNFT", "SIBN", "NVTK", "GAZP", "VTBR", "EUTR", "KMAZ", "FLOT", "HEAD",
          "ASTR", "SMLT", "LSRG", "PIKK", "ALRS", "RUAL"]


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


def save_all_json(tikers: list):
    """СОХРАНЯЕТ В JSON "tiker":"figi" """
    try:
        for tiker in tikers:
            tiker_figi[tiker] = get_figi(tiker=tiker, cl=cl)
        with open("tiker_figi.json", "w", encoding="utf-8") as f:
            json.dump(tiker_figi, f, indent=4, ensure_ascii=False, sort_keys=True)
        return None
    except Exception as e:
        logger.info(f" - функция save_all_json - не получается сохранить JSON.Exception as e : {e}")
        return None


if __name__ == "__main__":
    with Client(token) as cl:
        save_all_json(tikers=tikers)
