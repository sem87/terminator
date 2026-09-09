import os
from log.logicuber import system_log, debug_log, trade_log
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv("../terminator/.env.term")



class BuySellAktiv:
    def __init__(self, client, services) -> None:
        self.client = client
        self.services = services
        self.account_id = os.getenv("AOCID")

        if not self.account_id:
            system_log.warning("Переменная окружения AOCID не найдена!")

    def already_exist(self) -> dict:
        """ПОЛУЧАЕМ СЛОВАРЬ УЖЕ КУПЛЕННЫХ АКТИВОВ (ПОЗИЦИЙ В ПОРТФЕЛЕ)"""
        try:
            dict_already_exist = {}
            portfolio = self.services.operations.get_portfolio(account_id=self.account_id)
            for position in portfolio.positions:
                # Проверяем, что количество актива > 0 (учитываем и units, и nano)
                if position.quantity.units > 0 or position.quantity.nano > 0:
                    dict_already_exist[position.ticker] = {
                        "figi": position.figi,
                        "quantity_units": position.quantity.units,
                        "quantity_nano": position.quantity.nano
                    }
            trade_log.info(f"Уже в портфеле: {list(dict_already_exist.keys())}")
            debug_log.info(f"Уже в портфеле: {list(dict_already_exist.keys())}")
            return dict_already_exist

        except Exception as e:
            system_log.error(f"already_exist() ошибка в получении портфеля: {e}")
            return {}
