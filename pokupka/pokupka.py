from log.logicuber import system_log, debug_log,trade_log

class BuySellAktiv:
    def __init__(self,client,services) -> None:
        self.client = client  # Сам канал
        self.services = services  # Объект Services с методами API (instruments, orders и т.д.)


    # -------ФУНКЦИИ ПОКУПКИ ПРОДАЖИ ПЕРЕУСТАНОВКИ--------
    def already_exist(self) -> dict:
        """ПОЛУЧАЕМ СЛОВАРЬ АКТИВНЫХ ЗАЯВОК"""
        try:
            dict_already_exist = {}
            activ_orders = self.client.operations.get_portfolio(account_id=accid).positions
            for activ_order in activ_orders:
                dict_already_exist[activ_order.ticker] = activ_order.figi
            trade_log.info(f"Эти тикеры уже куплены {dict_already_exist}")
            return dict_already_exist
        except Exception as e:
            system_log.error(f"already_exist() ошибка в получении активных заявок : Exception as e : {e}")