from utils import *
from tiker_figi_json import *

# ВХОДНЫЕ ДАННЫЕ
# tiktok = ['SBER', 'ROSN', 'NVTK']
# на рынке     "на рынке"    "закрыто"
# tiktok = ['SBER', 'ROSN', 'NVTK', 'TATN', 'RNFT', 'SIBN', 'GAZP', 'VTBR', 'EUTR', 'ASTR', 'SMLT', 'PIKK', 'RUAL',
#           'PLZL', 'SELG', 'GMKN']
# все
tiktok = ["SBER", "ROSN", "LKOH", "ZAYM", "SNGS", "TATN", "BANE", "ELFV", "SLAV", "YAKG", "RNFT", "SIBN", "TGKN",
          "NVTK", "GAZP", "MOEX", "MBNK", "BSPB", "SPBE", "ZAYM", "RENI", "VTBR", "SVCB", "CBOM", "MGKL", "CARM",
          "MGNT", "GCHE", "KROT", "LENT", "SVAV", "AQUA", "HNFG", "BELU", "ABRD", "OKEY", "NKHP", "GTRK", "WUSH",
          "MSTT", "EUTR", "KMAZ", "FLOT", "FESH", "UWGN", "NMTP", "ABIO", "HEAD", "ASTR", "DELI", "LEAS", "KZIZ",
          "SMLT", "LSRG", "PIKK", "TGKJ", "VSMO", "PLZL", "AKRN", "LNZL", "CHMK", "PHOR", "CHMF", "KAZT", "ENPG",
          "NLMK", "GMKN", "NKNC", "KZOS", "MRKZ", "ALRS", "RUAL", "PRFN", "UGLD", "NSVZ", "RTKM", "CNTL", "TTLK",
          "VRSB", "PMSB", "KLSB", "LSNG", "IRAO", "DVEC", "UPRO", "MSRS", "MRKC", "MRKP", "MRKV", "MRKY", "T", "SELG","ASTR"]
# tikers = "SBER"
activity = "закрыто"
description = "vvv"


# ФУНКЦИИ
def add_line(tikers, price_mean, volume_mean, trade_sphere, activity, statistics, description, win_rate):
    """ДОБАВЛЯЕМ В БАЗУ analysis_tiker"""
    strok = session.query(AnalysisTiker.tiker).filter(AnalysisTiker.tiker == tikers).first()
    if strok:
        print(f"В базе {tikers} уже есть. Обновим данные")
        # Обновим данные
        update = session.query(AnalysisTiker).filter(AnalysisTiker.tiker == tikers).first()
        update.price_mean = price_mean
        update.volume_mean = volume_mean
        update.trade_sphere = trade_sphere
        update.statistics = statistics
        update.win_rate = win_rate
        session.commit()
    else:
        print(f"{tikers} - добавляем в базу")
        info_trade = AnalysisTiker(tiker=tikers, price_mean=price_mean, volume_mean=volume_mean,
                                   trade_sphere=trade_sphere, activity=activity, statistics=statistics,
                                   description=description, win_rate=win_rate)
        session.add(info_trade)
        session.commit()


def calculate_mean_param(df: pd.DataFrame, tiker: str) -> tuple:
    """Рассчитывает технические индикаторы для DataFrame"""
    """Расчитываем средние параметры"""
    try:
        mean_close = df["Закрытие"].mean()  # Цена закрытия средняя
        mean_volume = df["Объем"].mean()  # Объем средний
        return mean_close, mean_volume  # Возвращаем значения
    except:
        print("Ошибка calculate_mean_param()")


def statistics_win_rate(tikers):
    """Рассчитывает статистику и win/rate"""
    statistics = "статистика недоступна"
    win_rate = 0
    try:
        count_profit = (select(MyTradeResult.conclusion_trading,
                               func.count(MyTradeResult.conclusion_trading).label('count')).where(
            MyTradeResult.conclusion_trading == "прибыль").where(MyTradeResult.tiker == tikers).group_by(
            MyTradeResult.tiker, MyTradeResult.conclusion_trading))
        # Выполнение запроса
        results_profit = session.execute(count_profit).first()
        # -----------------------------------
        count_lesion = (select(MyTradeResult.conclusion_trading,
                               func.count(MyTradeResult.conclusion_trading).label('count')).where(
            MyTradeResult.conclusion_trading == "убыток").where(MyTradeResult.tiker == tikers).group_by(
            MyTradeResult.tiker, MyTradeResult.conclusion_trading))
        # Выполнение запроса
        results_lesion = session.execute(count_lesion).first()
        results_profit = results_profit if results_profit is not None else ("прибыль", 0)
        results_lesion = results_lesion if results_lesion is not None else ("убыток", 0)
        statistics = str(results_profit[0]) + " = " + str(results_profit[1]) + " ; " + str(
            results_lesion[0]) + " = " + str(results_lesion[1])
        # считаем win_rate
        if results_profit[1] == 0 and results_lesion[1] == 0:
            win_rate = 0
        else:
            win_rate = round((results_profit[1] / (results_lesion[1] + results_profit[1])) * 100, 2)
    except:
        print("ошибка statistics")
    return statistics, win_rate


def sector_trade(tikers, cl):
    """Узнает в каком секторе тикер"""
    sector_mapping = {"financial": "Банки / Финансы", "energy": "Нефтегаз / Энергетика",
                      "materials": "Металлы / Горнодобыча", "industrials": "Промышленность",
                      "consumer": "Потребительские товары", "consumer_staples": "Ритейл / Продукты",
                      "health_care": "Медицина / Фарма", "it": "IT / Технологии",
                      "telecom": "Телеком", "utilities": "Коммунальные услуги",
                      "real_estate": "Недвижимость", "": "Не определён", "other": "Прочее"}
    trade_sphere = "значение по умолчанию"
    try:
        # Получаем все акции рынка
        shares = cl.instruments.shares().instruments
        # Ищем тикер и получаем его class_code
        target = None
        for share in shares:
            if share.ticker == tikers.upper():
                target = share
                break
        if not target:
            return "не найден"
        # Теперь можем запросить детали с правильным class_code
        share = cl.instruments.share_by(id=tikers, class_code=target.class_code,
                                        id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER).instrument
        trade_sphere_eng = getattr(share, 'sector', '').strip()   # or "не определён"
        trade_sphere = sector_mapping[trade_sphere_eng]
    except Exception as e:
        print(f"ошибка в sector_trade - {e}")
    return trade_sphere


if __name__ == "__main__":
    """НАПИСАТЬ ЧТОБЫ ВСЕ ДАННЫЕ ПРОГА БРАЛА АВТОМАТИЧЕСКИ,ЧТОБЫ ПОДГРУЖАЛАСЬ СРЕДНЯЯ СТАТИСТИКА,
    НУЖНО ЧТОБЫ ВЫВОДИЛСЯ ИТОГОВЫЙ СПИСОК С ТИКЕРАМИ АКТИВНЫМИ"""
    for tikers in tiktok:
        with Client(token) as cl:
            # Узнаем из тикера фиги
            figs = get_figi(tiker=tikers, cl=cl)
            tuple_mean = calculate_mean_param(
                df=candl(cl=cl, day=50, interval=CandleInterval.CANDLE_INTERVAL_DAY.value, figi=figs, tiker=tikers),
                tiker=tikers)
            price_mean = round(tuple_mean[0], 2)
            volume_mean = round(tuple_mean[1] / 1000)
            # запрос для статистики ----------------------
            statistics = statistics_win_rate(tikers=tikers)[0]
            win_rate = statistics_win_rate(tikers=tikers)[1]
            # конец запрос для статистики ----------------------
            # сфера ---------------
            trade_sphere = sector_trade(tikers=tikers, cl=cl)
            add_line(tikers=tikers, price_mean=price_mean, volume_mean=volume_mean, trade_sphere=trade_sphere,
                     activity=activity, statistics=statistics, description=description, win_rate=win_rate)
            time.sleep(3)
    print(f"Эти акции торгуются на рынке - {list_active_tickers()}")
