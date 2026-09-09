import os
from log.logicuber import system_log, debug_log,trade_log
from dotenv import load_dotenv


# Загружаем переменные окружения
load_dotenv("../terminator/.env.term")




class BuySellAktiv:
    def __init__(self, client, services) -> None:
        if client is None:
            raise ValueError(
                "Ошибка инициализации: 'client' не может быть None. Проверьте, как вы создаёте экземпляр класса.")
        self.client = client
        self.services = services
        self.account_id = os.getenv("AOCID")

        if not self.account_id:
            system_log.warning("Переменная окружения AOCID не найдена!")

    def already_exist(self) -> dict:
        """ПОЛУЧАЕМ СЛОВАРЬ УЖЕ КУПЛЕННЫХ АКТИВОВ (ПОЗИЦИЙ В ПОРТФЕЛЕ)"""
        try:
            if self.client is None:
                system_log.error("already_exist(): self.client равен None")
                return {}

            dict_already_exist = {}

            # Получаем портфель (позиции), а не заявки
            portfolio = self.client.operations.get_portfolio(account_id=self.account_id)

            for position in portfolio.positions:
                # Проверяем, что количество актива > 0 (игнорируем нулевые позиции)
                if position.quantity.units > 0 or position.quantity.nano > 0:
                    dict_already_exist[position.ticker] = position.figi

            trade_log.info(f"************ Эти тикеры уже в портфеле: {dict_already_exist}")
            return dict_already_exist

        except Exception as e:
            system_log.error(f"already_exist() ошибка в получении портфеля: {e}")
            return {}

    # # Если вам НУЖНЫ именно АКТИВНЫЕ (неисполненные) ЗАЯВКИ, используйте этот метод:
    # def get_active_orders(self) -> dict:
    #     """ПОЛУЧАЕМ СЛОВАРЬ АКТИВНЫХ (НЕИСПОЛНЕННЫХ) ЗАЯВОК"""
    #     try:
    #         if self.client is None:
    #             return {}
    #
    #         dict_active_orders = {}
    #         orders_response = self.client.orders.get_orders(account_id=self.account_id)
    #
    #         for order in orders_response.orders:
    #             # order.instrument_id - это figi в t-invest API
    #             dict_active_orders[order.instrument_id] = order.order_id
    #
    #         trade_log.info(f"************ Активные заявки: {dict_active_orders}")
    #         return dict_active_orders
    #
    #     except Exception as e:
    #         system_log.error(f"get_active_orders() ошибка: {e}")
    #         return {}