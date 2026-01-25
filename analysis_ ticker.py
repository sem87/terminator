from utils import *
from tiker_figi_json import *

# ВХОДНЫЕ ДАННЫЕ
# tiktok = ["SBER", "ROSN", "SNGS", "TATN", "RNFT", "SIBN", "NVTK", "GAZP", "VTBR", "EUTR", "FLOT", "HEAD",
#           "ASTR", "SMLT", "LSRG", "PIKK", "ALRS", "RUAL", "PLZL", "SELG", "GMKN"]
tikers = "PLZL"
trade_sphere = "xxx"
activity = "на рынке"
statistics = "zzz"
description = "vvv"


# ФУНКЦИИ
def add_line(tikers, price_mean, volume_mean, trade_sphere, activity, statistics, description):
    """ДОБАВЛЯЕМ В БАЗУ analysis_tiker"""
    strok = session.query(AnalysisTiker.tiker).filter(AnalysisTiker.tiker == tikers).first()
    if strok:
        print(f"В базе {tikers} уже есть .Обновим данные")
        # Обновим данные
        update = session.query(AnalysisTiker).filter(AnalysisTiker.tiker == tikers).first()
        update.price_mean = price_mean
        update.volume_mean = volume_mean
        session.commit()
    else:
        print(f"{tikers} - добавляем в базу")
        info_trade = AnalysisTiker(tiker=tikers, price_mean=price_mean, volume_mean=volume_mean,
                                   trade_sphere=trade_sphere, activity=activity, statistics=statistics,
                                   description=description)
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


if __name__ == "__main__":
    """НАПИСАТЬ ЧТОБЫ ВСЕ ДАННЫЕ ПРОГА БРАЛА АВТОМАТИЧЕСКИ,ЧТОБЫ ПОДГРУЖАЛАСЬ СРЕДНЯЯ СТАТИСТИКА,
    НУЖНО ЧТОБЫ ВЫВОДИЛСЯ ИТОГОВЫЙ СПИСОК С ТИКЕРАМИ АКТИВНЫМИ"""
    # for tikers in tiktok:
    with Client(token) as cl:
        # Узнаем из тикера фиги
        figs = get_figi(tiker=tikers, cl=cl)
        tuple_mean = calculate_mean_param(
            df=candl(cl=cl, day=50, interval=CandleInterval.CANDLE_INTERVAL_DAY.value, figi=figs, tiker=tikers),
            tiker=tikers)
        price_mean = round(tuple_mean[0], 2)
        volume_mean = round(tuple_mean[1] / 1000)
        add_line(tikers=tikers, price_mean=price_mean, volume_mean=volume_mean, trade_sphere=trade_sphere,
                 activity=activity, statistics=statistics, description=description)
        print(list_active_tickers())
        time.sleep(3)
