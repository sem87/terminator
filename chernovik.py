import os
import time
import uuid
import math
from dotenv import load_dotenv

from t_tech.invest import (
    InstrumentIdType, OrderDirection, OrderType, OrderExecutionReportStatus,
    RequestError, StopOrderDirection, StopOrderExpirationType, StopOrderType, Quotation
)
from log.logicuber import system_log, debug_log, trade_log

load_dotenv("../terminator/.env.term")


def _quotation_to_float(quotation) -> float:
    """Безопасная конвертация объекта Quotation или MoneyValue в float"""
    return float(quotation.units) + float(quotation.nano) / 1_000_000_000


def _float_to_quotation(value: float) -> Quotation:
    """Конвертация float в объект Quotation для API Тинькофф"""
    units = int(value)
    nano = int(round((value % 1) * 1_000_000_000))
    return Quotation(units=units, nano=nano)


class BuySellAktiv:
    def __init__(self, client, services, summa_pokupki: float = 6600.0) -> None:
        self.client = client
        self.services = services
        self.summa_pokupki = float(summa_pokupki)
        self.account_id = os.getenv("AOCID")
        if not self.account_id:
            system_log.warning("BuySellAktiv __init__: Переменная окружения AOCID не найдена!")

    def already_exist(self) -> dict:
        """ПОЛУЧАЕМ СЛОВАРЬ УЖЕ КУПЛЕННЫХ АКТИВОВ"""
        try:
            dict_already_exist = {}
            portfolio = self.services.operations.get_portfolio(account_id=self.account_id)
            for position in portfolio.positions:
                if position.quantity.units > 0 or position.quantity.nano > 0:
                    qty_lots = int(round(_quotation_to_float(position.quantity_lots)))
                    avg_price = _quotation_to_float(position.average_position_price)
                    dict_already_exist[position.ticker] = {
                        "figi": position.figi,
                        "quantity_lots": qty_lots,
                        "avg_price": avg_price
                    }
            return dict_already_exist
        except Exception as e:
            system_log.error(f"BuySellAktiv в already_exist() ошибка: {e}")
            return {}

    def calculation_number_lots(self, figi: str, tiker: str) -> int:
        """РАСЧЕТ КОЛИЧЕСТВА ЛОТОВ С УЧЕТОМ ЗАПАСА НА КОМИССИЮ"""
        try:
            last_prices = self.services.market_data.get_last_prices(figi=[figi]).last_prices
            if not last_prices:
                return 0

            current_price = _quotation_to_float(last_prices[0].price)
            if current_price <= 0:
                return 0

            instrument = self.services.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi
            ).instrument
            lot_size = int(instrument.lot)
            price_per_lot = current_price * lot_size

            positions = self.services.operations.get_positions(account_id=self.account_id)
            available_money = 0.0
            for money in positions.money:
                if money.currency.lower() in ["rub", "rubl", "rur", ""]:
                    available_money = _quotation_to_float(money)
                    break

            if available_money == 0.0 and positions.money:
                available_money = _quotation_to_float(positions.money[0])

            # ВАЖНО: Оставляем 1% запаса на комиссию брокера и биржи
            budget = min(self.summa_pokupki, available_money) * 0.99

            if budget < price_per_lot:
                debug_log.info(f"{tiker}: Недостаточно средств. Бюджет: {budget:.2f}, Цена лота: {price_per_lot:.2f}")
                return 0

            quantity_lots = int(budget // price_per_lot)
            trade_log.info(f"{tiker}: Цена: {current_price}, Лот: {lot_size}, Лотов к покупке: {quantity_lots}")
            return quantity_lots
        except Exception as e:
            system_log.error(f"{tiker} - calculation_number_lots() ошибка: {e}")
            return 0

    def opredelaem_schag(self, figi: str, tiker: str) -> float:
        """ОПРЕДЕЛЕНИЕ ШАГА ЦЕНЫ"""
        try:
            instrument = self.services.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi
            ).instrument
            step = _quotation_to_float(instrument.min_price_increment)
            return step if step > 0 else 0.01
        except Exception as e:
            system_log.error(f"{tiker} - opredelaem_schag() ошибка: {e}")
            return 0.01

    def activ_pokupka(self, figi: str, tiker: str, existing_portfolio: dict | None = None):
        """ПОКУПКА АКТИВА И ВЫСТАВЛЕНИЕ СТОП-ОРДЕРОВ"""
        # 1. Проверка (используем переданный портфель, чтобы не спамить API)
        portfolio = existing_portfolio if existing_portfolio is not None else self.already_exist()
        if tiker in portfolio:
            trade_log.info(f"{tiker} - УЖЕ КУПЛЕНО, пропускаем.")
            return

        # 2. Расчёт лотов
        quantity = self.calculation_number_lots(figi=figi, tiker=tiker)
        if quantity <= 0:
            trade_log.info(f"НЕ КУПИЛИ {tiker}, кол-во лотов = {quantity}")
            return

        # 3. Выставление ордера
        order_id = str(uuid.uuid4())
        is_filled = False

        try:
            self.services.orders.post_order(
                figi=figi, quantity=quantity, direction=OrderDirection.ORDER_DIRECTION_BUY,
                order_type=OrderType.ORDER_TYPE_MARKET, account_id=self.account_id, order_id=order_id
            )
            trade_log.warning(f"ОРДЕР ВЫСТАВЛЕН: {tiker}. Кол-во: {quantity}")

            # 4. Опрос статуса
            max_wait_time, poll_interval, start_time = 20, 2, time.time()
            while time.time() - start_time < max_wait_time:
                order_state = self.client.orders.get_order_state(account_id=self.account_id, order_id=order_id)
                status = order_state.execution_report_status

                if status in (OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL,
                              OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_PARTIALLYFILL):
                    is_filled = True
                    break
                elif status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_REJECTED:
                    system_log.error(
                        f"ОРДЕР ОТКЛОНЁН: {tiker}. Причина: {getattr(order_state, 'message', 'Неизвестно')}")
                    break  # Прерываем цикл, is_filled останется False

                time.sleep(poll_interval)

            # КРИТИЧЕСКИ ВАЖНО: Если ордер не исполнен, прерываем функцию, чтобы не ставить стопы в воздух
            if not is_filled:
                system_log.warning(f"ОРДЕР НЕ ИСПОЛНЕН за {max_wait_time} сек: {tiker}. Стоп-ордера не выставлены.")
                return

        except RequestError as e:
            system_log.error(f"{tiker} - RequestError при покупке: {e}")
            return  # Прерываем при ошибке
        except Exception as e:
            system_log.error(f"{tiker} - Критическая ошибка при покупке: {e}")
            return  # Прерываем при ошибке

        # ==========================================================
        # 5. ВЫСТАВЛЕНИЕ ТЕЙК-ПРОФИТА И СТОП-ЛОССА (Только если покупка успешна)
        # ==========================================================
        time.sleep(1.5)  # ОДНОЙ паузы достаточно для обновления данных на сервере

        updated_portfolio = self.already_exist()
        pos_data = updated_portfolio.get(tiker)

        if not pos_data:
            system_log.error(f"{tiker} не найден в портфеле после успешной покупки. Стопы не выставлены.")
            return

        avg_price = pos_data["avg_price"]
        qty_lots = pos_data["quantity_lots"]
        step = self.opredelaem_schag(figi=figi, tiker=tiker)

        # Расчет цен
        coeff_tp = 1.01
        coeff_sl = 0.994

        raw_tp_price = avg_price * coeff_tp
        raw_sl_price = avg_price * coeff_sl

        valid_tp_price = math.ceil(raw_tp_price / step) * step
        valid_sl_price = math.floor(raw_sl_price / step) * step

        # ЗАЩИТА: Если из-за округления SL стал равен или выше цены покупки, сдвигаем его ниже
        if valid_sl_price >= avg_price:
            valid_sl_price = valid_sl_price - step
            system_log.warning(f"{tiker}: Стоп-лосс скорректирован до {valid_sl_price:.4f} во избежание ошибки 30035")

        tp_quotation = _float_to_quotation(valid_tp_price)
        sl_quotation = _float_to_quotation(valid_sl_price)

        try:
            # Тейк-Профит
            self.services.stop_orders.post_stop_order(
                figi=figi, quantity=qty_lots, price=tp_quotation, stop_price=tp_quotation,
                direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL, account_id=self.account_id,
                expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
                stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT,
            )
            debug_log.warning(f"✅ ТЕЙК-ПРОФИТ: {tiker} | Цена: {valid_tp_price:.4f} | Лотов: {qty_lots}")

            # Стоп-Лосс
            self.services.stop_orders.post_stop_order(
                figi=figi, quantity=qty_lots, price=sl_quotation, stop_price=sl_quotation,
                direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL, account_id=self.account_id,
                expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
                stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS,
            )
            # ИСПРАВЛЕНО: теперь логируется valid_sl_price, а не valid_tp_price
            debug_log.warning(f"🛡️ СТОП-ЛОСС: {tiker} | Цена: {valid_sl_price:.4f} | Лотов: {qty_lots}")

        except Exception as e:
            system_log.error(f"{tiker} - Ошибка при выставлении стоп-ордеров: {e}")