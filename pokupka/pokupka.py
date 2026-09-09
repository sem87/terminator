import os
from log.logicuber import system_log, debug_log, trade_log
from dotenv import load_dotenv
from t_tech.invest import InstrumentIdType  # Добавлен необходимый импорт

load_dotenv("../terminator/.env.term")


def _quotation_to_float(quotation) -> float:
    """Безопасная конвертация объекта Quotation в float"""
    return float(quotation.units) + float(quotation.nano) / 1_000_000_000


class BuySellAktiv:
    def __init__(self, client, services, summa_pokupki: float = 6600.0) -> None:
        self.client = client
        self.services = services
        self.summa_pokupki = float(summa_pokupki)
        self.account_id = os.getenv("AOCID")
        if not self.account_id:
            system_log.warning("BuySellAktiv __init__: Переменная окружения AOCID не найдена!")

    def already_exist(self) -> dict:
        """ПОЛУЧАЕМ СЛОВАРЬ УЖЕ КУПЛЕННЫХ АКТИВОВ (ПОЗИЦИЙ В ПОРТФЕЛЕ)"""
        try:
            dict_already_exist = {}
            portfolio = self.services.operations.get_portfolio(account_id=self.account_id)
            for position in portfolio.positions:
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
            system_log.error(f"BuySellAktiv в already_exist() ошибка в получении портфеля: {e}")
            return {}

    def calculation_number_lots(self, figi: str, tiker: str) -> int:
        """РАСЧЕТ КОЛИЧЕСТВА ЛОТОВ НА СУММУ self.summa_pokupki"""
        try:
            # 1. Получаем текущую цену инструмента
            last_prices = self.services.market_data.get_last_prices(figi=[figi]).last_prices
            if not last_prices:
                system_log.warning(f"{tiker}: Не удалось получить последнюю цену.")
                return 0

            current_price = _quotation_to_float(last_prices[0].price)
            if current_price <= 0:
                system_log.warning(f"{tiker}: Некорректная цена {current_price}")
                return 0

            # 2. Получаем информацию о размере лота
            instrument = self.services.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                id=figi
            ).instrument
            lot_size = int(instrument.lot)
            price_per_lot = current_price * lot_size

            # 3. Получаем доступные деньги на счете
            positions = self.services.operations.get_positions(account_id=self.account_id)

            available_money = 0.0
            for money in positions.money:
                # Ищем рубли (учитываем разные варианты написания валюты)
                if money.currency.lower() in ["rub", "rubl", "rur", ""]:
                    available_money = _quotation_to_float(money)
                    break

            # Если рубли не найдены, берем первый попавшийся баланс (фоллбек)
            if available_money == 0.0 and positions.money:
                available_money = _quotation_to_float(positions.money[0])
                system_log.warning(
                    f"{tiker}: Валюта RUB не найдена, используем баланс {positions.money[0].currency}: {available_money}")

            # 4. Расчет количества лотов
            # Мы не можем потратить больше, чем есть на счете, и не больше лимита summa_pokupki
            budget = min(self.summa_pokupki, available_money)

            if budget < price_per_lot:
                debug_log.info(f"{tiker}: Недостаточно средств. Доступно: {budget:.2f}, Цена лота: {price_per_lot:.2f}")
                return 0

            # Целочисленное деление автоматически округляет вниз до целого числа лотов
            quantity_lots = int(budget // price_per_lot)

            debug_log.info(
                f"{tiker}: Цена: {current_price}, Лот: {lot_size}, Цена лота: {price_per_lot:.2f}, Бюджет: {budget:.2f}, Лотов к покупке: {quantity_lots}")
            return quantity_lots

        except Exception as e:
            system_log.error(f"{tiker} - BuySellAktiv calculation_number_lots() ошибка: {e}")
            return 0




