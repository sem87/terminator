from actualnost_ticker.actualnost import ActualniiTiker,token




if __name__ == "__main__":
    # ==========НАЧАЛО РОБОТЫ С JSON и подготовка работы с актуальными тикерами и их FIGI. ============
    with ActualniiTiker(token=token,days=3) as actual_tiker:
        # Проверяем актуальность
        # actual_tiker.last_modified_json()
        print(actual_tiker)
        actual_tiker.list_active_tickers()
        # # Читаем данные
        # print(actual_tiker.read_tiker_figi_json())

    # ==========КОНЕЦ РОБОТЫ С JSON и подготовка работы с актуальными тикерами и их FIGI. ============

