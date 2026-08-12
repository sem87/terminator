#УНИВЕРСАЛЬНЫЙ РОБОТ ДЛЯ ПОКУПКИ ПРОДАЖИ АКЦИЙ , АНАЛИЗА ТОРГОВЛИ, ВНЕСЕНИЕ СОПУТСТВУЮЩИХ АКТИВОВ
import time
from t_tech.invest import CandleInterval, Client
from log.logger import inform, logger
import os
from dotenv import load_dotenv
from actualnost_ticker.actualnost import ActualniiTiker,token

# # ========НАЧАЛО ПОДГОТОВКИ===========
# """ДЛЯ ЧТЕНИЯ ТОКЕНА"""
# load_dotenv("../terminator/.env.term")  # Если файл в той же папке, что и скрипт
# token = os.getenv("TOKSELL")  # Обратите внимание на имя переменной
# accid = os.getenv("AOCID")  # Обратите внимание на имя переменной
# telegtok = os.getenv("TELEGTOKENG")
# groupt = os.getenv("GROUPT")
# api_iddd = os.getenv("API_IDDD")
# proxy_url = os.getenv("PROXY_URL")
# # -----------СЛОВАРИ---------
# buy_day = {}
# buy_hour = {}
# buy_15min = {}
# buy_itog = {}
# sale_day = {}
# sale_hour = {}
# sale_15min = {}
# sale_itog = {}
# # -----------ТИКЕРЫ ДЛЯ РАБОТЫ---------
# tiker_figi = {}
# # ========КОНЕЦ ПОДГОТОВКИ===========



# -------------------РАБОТА С JSON И ПОДГОТОВКА СЛОВАРЕЙ-------------








if __name__ == "__main__":
    # Создаём экземпляр класса
    with ActualniiTiker(token=token,days=5) as actual_tiker:
        # Проверяем актуальность
        actual_tiker.last_modified_json()

        # # Читаем данные
        # print(actual_tiker.read_tiker_figi_json())



