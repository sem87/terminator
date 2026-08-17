from actualnost_ticker.actualnost import ActualniiTiker, token

if __name__ == "__main__":
    # ==========НАЧАЛО РОБОТЫ С JSON и подготовка работы с актуальными тикерами и их FIGI. ============
    with ActualniiTiker(token=token, days=7) as actual_tiker:
        # Проверяем актуальность
        actual_tiker.last_modified_json()
        # =========================================
        # Можно узнать тикер по фиги
        # print(actual_tiker.get_figi(tiker="TGLD@"))
        # Можно вытащить из базы sql_terminator все "на рынке"
        # actual_tiker.list_active_tickers()
        # Можно прочитать read_tiker_figi_json()
        # print(actual_tiker.read_tiker_figi_json())
        #==========================================
    # ==========КОНЕЦ РОБОТЫ С JSON и подготовка работы с актуальными тикерами и их FIGI. ============
