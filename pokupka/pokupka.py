import os
from log.logicuber import system_log, debug_log, trade_log
from dotenv import load_dotenv
from t_tech.invest import InstrumentIdType, InstrumentIdType, OrderDirection, OrderType, OrderExecutionReportStatus, \
    RequestError, StopOrderDirection, StopOrderExpirationType, StopOrderType, Quotation  # Добавлен необходимый импорт

import time
import uuid
import math
from decimal import ROUND_HALF_UP, Decimal

load_dotenv("../terminator/.env.term")


def _quotation_to_float(quotation) -> float:
    """Безопасная конвертация объекта Quotation в float"""
    return float(quotation.units) + float(quotation.nano) / 1_000_000_000


def _float_to_quotation(value: float) -> Quotation:
    """Конвертация обычного float в объект Quotation для API Тинькофф"""
    units = int(value)
    nano = int(round((value % 1) * 1_000_000_000))
    return Quotation(units=units, nano=nano)


class BuySellAktiv:
    def __init__(self, client, services, summa_pokupki: float = 6600.0) -> None:
        self.client = client
        self.services = services
        # print(f"::::::::::::клиент прямо в классе {self.client}")
        # print(f"::::::::::сервисес прямо в классе {self.services}")
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
                    # quantity_lots — это объект Quotation. Конвертируем и округляем до целого
                    qty_lots = int(round(_quotation_to_float(position.quantity_lots)))
                    avg_price = _quotation_to_float(
                        position.average_position_price)  # почему не нужно мне разделять так ли мне нужно
                    dict_already_exist[position.ticker] = {
                        "figi": position.figi,
                        "quantity_lots": qty_lots,
                        "avg_price": avg_price
                    }
                    # dict_already_exist[position.ticker] = {
                    #     "figi": position.figi,
                    #     "quantity_units": position.quantity.units,
                    #     "quantity_nano": position.quantity.nano
                    # }
            # trade_log.info(f"Уже в портфеле: {list(dict_already_exist.keys())}")
            # debug_log.info(f"Уже в портфеле: {list(dict_already_exist.keys())}")
            return dict_already_exist
        except Exception as e:
            system_log.error(f"BuySellAktiv в already_exist() ошибка в получении портфеля: {e}")
            return {}

    def calculation_number_lots(self, figi: str, tiker: str) -> int:
        """РАСЧЕТ КОЛИЧЕСТВА ЛОТОВ НА СУММУ self.summa_pokupki"""
        # нужно проверить функцию как она округляет
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
            trade_log.info(
                f"{tiker}: Цена: {current_price}, Лот: {lot_size}, Цена лота: {price_per_lot:.2f}, Бюджет: {budget:.2f}, Лотов к покупке: {quantity_lots}")
            return quantity_lots
        except Exception as e:
            system_log.error(f"{tiker} - BuySellAktiv calculation_number_lots() ошибка: {e}")
            return 0

    def opredelaem_schag(self, figi: str, tiker: str) -> float:
        """ОПРЕДЕЛЕНИЕ ШАГА ЦЕНЫ (min_price_increment) ДЛЯ КОНКРЕТНОГО АКТИВА"""
        try:
            instrument = self.services.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                id=figi
            ).instrument
            # min_price_increment — это Quotation. Используем нашу функцию конвертации
            step = _quotation_to_float(instrument.min_price_increment)
            if step <= 0:
                system_log.warning(f"{tiker}: Шаг цены равен 0, используем фоллбек 0.01")
                return 0.01
            debug_log.info(f"{tiker}: Шаг цены (min_price_increment) = {step}")
            return step
        except Exception as e:
            system_log.error(f"{tiker} - opredelaem_schag() ошибка: {e}")
            return 0.01  # Безопасный фоллбек

    def activ_pokupka(self, figi: str, tiker: str):
        """ПОКУПКА АКТИВА, РАССТОНОВКА СТОП-ЛОСА И ТЕЙК-ПРОФИТА"""
        try:
            # 1. ПРОВЕРКА: КУПЛЕН УЖЕ АКТИВ ИЛИ НЕТ
            if tiker in self.already_exist():
                trade_log.info(f"{tiker} - УЖЕ КУПЛЕНО")
                return
            # 2. РАСЧЁТ КОЛИЧЕСТВА ЛОТОВ
            quantity = self.calculation_number_lots(figi=figi, tiker=tiker)
            if quantity <= 0:
                trade_log.info(f"НЕ КУПИЛИ - {tiker}, т.к. можно купить {quantity} шт")
                return
            # 3. ГЕНЕРАЦИЯ УНИКАЛЬНОГО order_id ДЛЯ ИДЕМПОТЕНТНОСТИ
            order_id = str(uuid.uuid4())
            # 4 сама покупка
            try:
                self.services.orders.post_order(
                    figi=figi,
                    quantity=quantity,
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    account_id=self.account_id,  # Убедись, что ты передаешь это при создании BuySellAktiv
                    order_id=order_id
                )
                trade_log.warning(f"ОРДЕР ВЫСТАВЛЕН - {tiker}. Кол-во: {quantity}")
                # 5.=====НАЧАЛО ОПРОС СТАТУСА ОРДЕРА (вместо time.sleep(25)) =======
                max_wait_time = 26  # максимальное время ожидания в секундах
                poll_interval = 2  # интервал опроса в секундах
                start_time = time.time()
                is_filled = False
                while time.time() - start_time < max_wait_time:
                    order_state = self.client.orders.get_order_state(
                        account_id=self.account_id,
                        order_id=order_id)
                    status = order_state.execution_report_status
                    # Ордер исполнен или частично исполнен
                    if status in (
                            OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL,
                            OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_PARTIALLYFILL):
                        debug_log.info(f"ОРДЕР ИСПОЛНЕН - {tiker}. Статус: {status}")
                        is_filled = True
                        break
                    # Ордер отклонён биржей или брокером
                    elif status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_REJECTED:
                        system_log.error(
                            f"ОРДЕР ОТКЛОНЁН - {tiker}. Причина: {getattr(order_state, 'message', 'Неизвестно')}")
                        break
                    # Ждём перед следующей проверкой
                    time.sleep(poll_interval)
                if not is_filled:
                    system_log.warning(
                        f"ОРДЕР НЕ ИСПОЛНЕН за {max_wait_time} сек - {tiker}. Проверьте статус вручную.")
                # 5.=====КОНЕЦ ОПРОС СТАТУСА ОРДЕРА (вместо time.sleep(25)) =======
            except RequestError as e:
                system_log.info(f"{tiker} - BuySellAktiv activ_pokupka() RequestError: {e}")
                if e.details == 30015:
                    system_log.info(f"{tiker} - Некорректное количество лотов: {quantity} шт. Ошибка 30015")
            except Exception as e:
                system_log.info(f"{tiker} - BuySellAktiv activ_pokupka() ошибка в выставлении ордера: {e}")
        except Exception as e:
            system_log.info(f"{tiker} - BuySellAktiv  activ_pokupka() ошибка при покупки актива : Exception as e : {e}")

        # стоп и тейк вынести в отдельные функции с указаниями отдельно размера
        """==========ИНФОРМАЦИЯ О ПОЗИЦИИ НА СЧЕТЕ.ЗА СКОЛЬКО КУПИЛИ И ЛОТНОСТЬ=========="""
        # Получаем информацию о позициях на счёте
        # 5. Выставление Тейк-Профита (только если покупка успешна)
        # Запрашиваем обновленный портфель, чтобы получить точную среднюю цену и кол-во лотов после сделки
        time.sleep(2)  # убрать это время похоже нужно
        updated_portfolio = self.already_exist()
        pos_data = updated_portfolio.get(tiker)
        if not pos_data:
            system_log.error(f"{tiker} не найден в портфеле после покупки. Тейк-профит не выставлен.")
            return
        avg_price = pos_data["avg_price"]
        qty_lots = pos_data["quantity_lots"]

        """НАЧАЛО РАСЧЕТ ПАРАМЕТРОВ ДЛЯ ЗАЯВОК"""
        # !!! переделать значение тейк профит , брать его исходя из атр и р:р
        time.sleep(2)
        # 1. Получаем шаг цены через метод класса
        step = self.opredelaem_schag(figi=figi, tiker=tiker)
        # 2. Рассчитываем целевую цену тейк-профита (например, +5%)
        coeff_take_profit = 1.01
        coeff_stop_loss_price = 0.994  # СДЕЛАЕМ W/R 1:1 (0,34%)
        raw_tp_price = avg_price * coeff_take_profit
        raw_sl_price = avg_price * coeff_stop_loss_price
        # 3. МАГИЯ ОКРУГЛЕНИЯ до шага биржи
        # Пример: цена 52.867, шаг 0.01 -> round(5286.7) * 0.01 = 52.87
        # Для Take-Profit (цена ВЫШЕ) → округляем ВВЕРХ
        valid_tp_price = math.ceil(raw_tp_price / step) * step
        # Для Stop-Loss (цена НИЖЕ) → округляем ВНИЗ
        valid_sl_price = math.floor(raw_sl_price / step) * step
        # 4. Конвертируем в Quotation для API
        tp_quotation = _float_to_quotation(valid_tp_price)
        sl_quotation = _float_to_quotation(valid_sl_price)
        # Стоп-лимит заявка (продажа при достижении take_profit_price)
        """КОНЕЦ РАСЧЕТ ПАРАМЕТРОВ ДЛЯ ЗАЯВОК"""
        """НАЧАЛО ТЕЙК-ПРОФИТ ЗАЯВКИ"""  # продажа при достижении take_profit_price
        time.sleep(2)
        self.services.stop_orders.post_stop_order(
            figi=figi,
            quantity=qty_lots,  # Это int (количество лотов)
            price=tp_quotation,  # <-- ИСПРАВЛЕНО
            stop_price=tp_quotation,  # <-- ИСПРАВЛЕНО
            direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
            account_id=self.account_id,
            expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
            stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT, )
        debug_log.warning(f"ТЕЙК-ПРОФИТ выставлен: {tiker} | Цена: {valid_tp_price:.4f} | Лотов: {qty_lots}")
        # except RequestError as e:
        # system_log.error(f"{tiker} - RequestError при покупке: {e}")
        # except Exception as e:
        #     system_log.error(f"{tiker} - Критическая ошибка в activ_pokupka: {e}")
        """КОНЕЦ ТЕЙК-ПРОФИТ ЗАЯВКИ"""
        """НАЧАЛО СТОП-ЛОСС ЗАЯВКИ"""
        time.sleep(2)
        self.services.stop_orders.post_stop_order(
            figi=figi,
            quantity=qty_lots,  # Это int (количество лотов)
            price=sl_quotation,  # <-- ИСПРАВЛЕНО
            stop_price=sl_quotation,  # <-- ИСПРАВЛЕНО
            direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
            account_id=self.account_id,
            expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
            stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS)
        debug_log.warning(f"СТОП-ЛОСС выставлен: {tiker} | Цена: {valid_tp_price:.4f} | Лотов: {qty_lots}")
        # STOP_ORDER_TYPE_STOP_LIMIT    ИЛИ  STOP_ORDER_TYPE_STOP_LOSS
        """КОНЕЦ СТОП-ЛОСС ЗАЯВКИ"""