import os
from log.logicuber import system_log, debug_log, trade_log
from dotenv import load_dotenv
from t_tech.invest import InstrumentIdType, OrderDirection, OrderType, OrderExecutionReportStatus, \
    RequestError, StopOrderDirection, StopOrderExpirationType, StopOrderType, Quotation  # Добавлен необходимый импорт

import time
import uuid
# import math
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR,ROUND_HALF_UP

load_dotenv("../terminator/.env.term")


# def _quotation_to_float(quotation) -> float:
#     """Безопасная конвертация объекта Quotation в float"""
#     return float(quotation.units) + float(quotation.nano) / 1_000_000_000
#
#
# def _float_to_quotation(value: float) -> Quotation:
#     """Конвертация обычного float в объект Quotation для API Тинькофф"""
#     units = int(value)
#     nano = int(round((value % 1) * 1_000_000_000))
#     return Quotation(units=units, nano=nano)

def _quotation_to_float(quotation) -> Decimal:     # _quotation_to_decimal
    return Decimal(quotation.units) + Decimal(quotation.nano) / Decimal('1_000_000_000')

def _float_to_quotation(value: Decimal) -> Quotation:     # _decimal_to_quotation
    # value должно быть положительным для цен/количества
    units = int(value)
    nano = int((value - units) * Decimal('1_000_000_000'))
    return Quotation(units=units, nano=nano)



class BuySellAktiv:
    def __init__(self, client, services, summa_pokupki: float = 6600.0) -> None:
        self.client = client
        self.services = services
        self.summa_pokupki = Decimal(str(summa_pokupki))
        self.account_id = os.getenv("AOCID")
        if not self.account_id:
            system_log.warning("BuySellAktiv __init__: Переменная окружения AOCID не найдена!")
        self.IGNORE_STOP_LOSS_TICKERS = {"RUB000UTSTOM", "RUB", "USD000UTSTOM", "EUR000UTSTOM"}
        # Правила переноса стопа: (мин. мультипликатор, макс. мультипликатор, новый мультипликатор стопа, текст для лога)
        self.STOP_LOSS_RULES = [
            (1.0038, 1.0080, 1.0034, "0.34%"),
            (1.0080, 1.0150, 1.0070, "0.70%"),
            (1.0150, 1.0220, 1.0130, "1.30%"),
            (1.0220, 1.0310, 1.0200, "2.00%"),
            (1.0310, 1.0410, 1.0300, "3.00%"),
            (1.0410, 1.0450, 1.0400, "4.00%"),
        ]

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
            available_money = Decimal('0')
            for money in positions.money:
                # Ищем рубли (учитываем разные варианты написания валюты)
                if money.currency.lower() == "RUB":
                    available_money = _quotation_to_float(money)
                    break
            # Если рубли не найдены, берем первый попавшийся баланс (фоллбек)
            if available_money == Decimal('0') and positions.money:
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

    def opredelaem_schag(self, figi: str, tiker: str) -> Decimal:
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
                return Decimal('0.01')
            debug_log.info(f"{tiker}: Шаг цены (min_price_increment) = {step}")
            return step
        except Exception as e:
            system_log.error(f"{tiker} - opredelaem_schag() ошибка: {e}")
            return Decimal('0.01')  # Безопасный фоллбек

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
                order_response = self.services.orders.post_order(
                    figi=figi,
                    quantity=quantity,
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    account_id=self.account_id,  # Убедись, что ты передаешь это при создании BuySellAktiv
                    order_id=order_id
                )
                trade_log.warning(f"ОРДЕР ВЫСТАВЛЕН - {tiker}. Кол-во: {quantity}")

                # ВАЖНО: Берем реальный ID из ответа брокера что бы не было ошибки 50005
                actual_order_id = order_response.order_id
                debug_log.info(f"!!!!!!!!!!!Присвоен order_id: {actual_order_id}")
                # 5.=====НАЧАЛО ОПРОС СТАТУСА ОРДЕРА (вместо time.sleep(25)) =======
                max_wait_time = 26  # максимальное время ожидания в секундах
                poll_interval = 2  # интервал опроса в секундах
                start_time = time.time()
                is_filled = False
                while time.time() - start_time < max_wait_time:
                    order_state = self.services.orders.get_order_state(
                        account_id=self.account_id,
                        order_id=actual_order_id)
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
                    system_log.warning(f"ОРДЕР НЕ ИСПОЛНЕН за {max_wait_time} сек - {tiker}. Проверьте статус вручную.")
                    return
                # 5.=====КОНЕЦ ОПРОС СТАТУСА ОРДЕРА (вместо time.sleep(25)) =======
            except RequestError as e:
                system_log.info(f"{tiker} - BuySellAktiv activ_pokupka() RequestError: {e}")
                if e.details == 30015:
                    system_log.info(f"{tiker} - Некорректное количество лотов: {quantity} шт. Ошибка 30015")

            except Exception as e:
                system_log.info(f"{tiker} - BuySellAktiv activ_pokupka() ошибка в выставлении ордера на покупку: {e}")
                return  # Прерываем при ошибке
        except Exception as e:
            system_log.info(f"{tiker} - BuySellAktiv  activ_pokupka() ошибка при покупки актива : Exception as e : {e}")
            return  # Прерываем при ошибке

        # стоп и тейк вынести в отдельные функции с указаниями отдельно размера
        """==========ИНФОРМАЦИЯ О ПОЗИЦИИ НА СЧЕТЕ.ЗА СКОЛЬКО КУПИЛИ И ЛОТНОСТЬ=========="""
        # Получаем информацию о позициях на счёте
        # 5. Выставление Тейк-Профита (только если покупка успешна)
        # Запрашиваем обновленный портфель, чтобы получить точную среднюю цену и кол-во лотов после сделки
        try:
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
            # 1. Получаем шаг цены через метод класса
            step = self.opredelaem_schag(figi=figi, tiker=tiker)
            # 2. Рассчитываем целевую цену тейк-профита (например, +5%)
            coeff_take_profit = Decimal('1.01')
            coeff_stop_loss_price = Decimal('0.994')
            # coeff_take_profit = 1.01
            # coeff_stop_loss_price = 0.994  # СДЕЛАЕМ W/R 1:1 (0,34%)
            raw_tp_price = avg_price * coeff_take_profit
            raw_sl_price = avg_price * coeff_stop_loss_price
            # 3. МАГИЯ ОКРУГЛЕНИЯ до шага биржи
            # Пример: цена 52.867, шаг 0.01 -> round(5286.7) * 0.01 = 52.87
            # Для Take-Profit (цена ВЫШЕ) → округляем ВВЕРХ
            # valid_tp_price = math.ceil(raw_tp_price / step) * step
            valid_tp_price = (raw_tp_price / step).to_integral_value(rounding=ROUND_CEILING) * step
            # Для Stop-Loss (цена НИЖЕ) → округляем ВНИЗ
            # valid_sl_price = math.floor(raw_sl_price / step) * step
            # Округление ВНИЗ для Stop-Loss
            valid_sl_price = (raw_sl_price / step).to_integral_value(rounding=ROUND_FLOOR) * step


            # 4. Конвертируем в Quotation для API
            tp_quotation = _float_to_quotation(valid_tp_price)
            sl_quotation = _float_to_quotation(valid_sl_price)
            # Стоп-лимит заявка (продажа при достижении take_profit_price)
            """КОНЕЦ РАСЧЕТ ПАРАМЕТРОВ ДЛЯ ЗАЯВОК"""
            """НАЧАЛО ТЕЙК-ПРОФИТ ЗАЯВКИ"""  # продажа при достижении take_profit_price
            time.sleep(1)
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
            """КОНЕЦ ТЕЙК-ПРОФИТ ЗАЯВКИ"""
            """НАЧАЛО СТОП-ЛОСС ЗАЯВКИ"""
            self.services.stop_orders.post_stop_order(
                figi=figi,
                quantity=qty_lots,  # Это int (количество лотов)
                price=sl_quotation,  # <-- ИСПРАВЛЕНО
                stop_price=sl_quotation,  # <-- ИСПРАВЛЕНО
                direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                account_id=self.account_id,
                expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
                stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS)
            debug_log.warning(f"СТОП-ЛОСС выставлен: {tiker} | Цена: {valid_sl_price:.4f} | Лотов: {qty_lots}")
            # STOP_ORDER_TYPE_STOP_LIMIT    ИЛИ  STOP_ORDER_TYPE_STOP_LOSS
            """КОНЕЦ СТОП-ЛОСС ЗАЯВКИ"""
        except Exception as e:
            system_log.info(
                f"{tiker} - BuySellAktiv  activ_pokupka() ошибка при расстановке СТОП-ЛОСА И ТЕЙК-ПРОФИТА: Exception as e : {e}")


    def price_active_stop_loss(self, figi: str, tiker: str) -> Decimal | None:  # <-- ИСПРАВЛЕНО
        """ПОЛУЧАЕМ ЦЕНУ ИСПОЛНЕНИЯ АКТИВНОЙ СТОП-ЗАЯВКИ (Stop-Loss)"""
        try:
            # Получаем список активных стоп-заявок
            response = self.services.stop_orders.get_stop_orders(account_id=self.account_id)
            # Ищем именно Stop-Loss на продажу
            for stop in response.stop_orders:
                if (stop.figi == figi and
                        stop.direction == StopOrderDirection.STOP_ORDER_DIRECTION_SELL and
                        stop.order_type == StopOrderType.STOP_ORDER_TYPE_STOP_LOSS):
                    # Возвращаем цену как float
                    return _quotation_to_float(stop.stop_price)
            # Если стоп не найден
            return None
        except Exception as e:
            system_log.error(f"{tiker} - price_active_stop_loss() ошибка получения цены СТОП-ЛОСА: {e}")
            return None

    # def moving_stop_los(self, figi: str, tiker: str, quantity: int, avg_price: float, coeff_sl_price: float,
    #                     schag: float):
    def moving_stop_los(self, figi: str, tiker: str, quantity: int, avg_price: Decimal, coeff_sl_price: Decimal,schag: Decimal):
        """ОТМЕНА АКТИВНОГО СТОП-ЛОССА И ПЕРЕДВИГАНИЕ ЕГО НА НОВЫЙ УРОВЕНЬ"""
        try:
            # 1. ПОИСК И ОТМЕНА СТАРОГО СТОП-ЛОССА
            response = self.services.stop_orders.get_stop_orders(account_id=self.account_id)
            for stop in response.stop_orders:
                if (stop.figi == figi and
                        stop.direction == StopOrderDirection.STOP_ORDER_DIRECTION_SELL and
                        stop.order_type == StopOrderType.STOP_ORDER_TYPE_STOP_LOSS):
                    # Отменяем найденный стоп-ордер
                    self.services.stop_orders.cancel_stop_order(
                        account_id=self.account_id,
                        stop_order_id=stop.stop_order_id
                    )
                    trade_log.info(f"{tiker} - Старый стоп-лосс (ID: {stop.stop_order_id}) успешно отменен.")
                    break  # Прерываем цикл, так как нужный ордер найден и отменен

            # 2. РАСЧЕТ НОВОЙ ЦЕНЫ СТОП-ЛОССА
            # Базовая цена стопа
            raw_sl_price = avg_price * coeff_sl_price
            # Округляем ВНИЗ до ближайшего шага цены (безопаснее для стоп-лосса, чтобы не завысить цену срабатывания)
            # math.floor уже импортирован в твоем файле
            # valid_sl_price = math.floor(raw_sl_price / schag) * schag
            valid_sl_price = (raw_sl_price / schag).to_integral_value(rounding=ROUND_FLOOR) * schag
            # Конвертируем float в Quotation для API Тинькофф
            sl_quotation = _float_to_quotation(valid_sl_price)
            # 3. ВЫСТАВЛЕНИЕ НОВОГО СТОП-ЛОССА
            self.services.stop_orders.post_stop_order(
                figi=figi,
                quantity=quantity,
                price=sl_quotation,
                stop_price=sl_quotation,
                direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                account_id=self.account_id,
                expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
                stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS,
            )
            trade_log.info(f"{tiker} - НОВЫЙ СТОП-ЛОСС установлен: {valid_sl_price:.4f} | Лотов: {quantity}")
        except Exception as e:
            system_log.error(f"{tiker} - moving_stop_los() критическая ошибка при передвигании стоп-лосса: {e}",
                             exc_info=True)

    def resetting_stop_los(self):
        """ОПРЕДЕЛЯЕМ ГДЕ ПО ФАКТУ НАХОДИТСЯ ЦЕНА И В СООТВЕТСТВИИ ПЕРЕСТАВЛЯЕМ СТОП-ЛОС"""
        try:
            # Получаем актуальный словарь позиций из твоего же метода
            portfolio_dict = self.already_exist()
            if not portfolio_dict:
                return

            for current_tiker, pos_data in portfolio_dict.items():
                try:
                    # === НОВОЕ: Исключение для фондов ликвидности и валют ===
                    if current_tiker in self.IGNORE_STOP_LOSS_TICKERS:
                        debug_log.info(f"{current_tiker} - Пропускаем управление стоп-лоссом (исключенный актив).")
                        continue
                    # =========================================================
                    pos_figi = pos_data["figi"]
                    qty_lots = pos_data["quantity_lots"]
                    avg_price = pos_data["avg_price"]  # Уже float благодаря _quotation_to_float
                    if qty_lots <= 0:
                        continue
                    # 1. Получение текущей цены
                    last_prices_resp = self.services.market_data.get_last_prices(figi=[pos_figi])
                    if not last_prices_resp.last_prices:
                        continue
                    current_price = _quotation_to_float(last_prices_resp.last_prices[0].price)
                    # 2. Получение шага цены и текущего стопа
                    schag = self.opredelaem_schag(figi=pos_figi, tiker=current_tiker)
                    execution_price = self.price_active_stop_loss(figi=pos_figi, tiker=current_tiker)
                    if execution_price is None:
                        # continue  # Если активный стоп не найден, ставим стоп лос какой должен быть
                        system_log.error(
                            f" {current_tiker} BuySellAktiv resetting_stop_los - не был поставлен стоп-лосс ставим")
                        system_log.error(
                            f" {current_tiker} BuySellAktiv resetting_stop_los - ОБЯЗАТЕЛЬНО ПОДУМАЙ НУЖНО ЛИ ВЫСТАВЛЯТЬ СТОП-ЛОСС")
                        continue
                    # print(f"!!!!!!!!!!!!!!{current_tiker} купили по {avg_price} кол-во {qty_lots}  а -  сейчас цена {current_price}    цена стоп-лоса {execution_price}")
                    # 3. Проверка условий для переноса стопа
                    moved = False
                    for min_mult, max_mult, new_stop_mult, log_msg in STOP_LOSS_RULES:
                        trigger_min = avg_price * Decimal(str(min_mult))
                        trigger_max = avg_price * Decimal(str(max_mult))
                        # Условие: текущий стоп ниже порога И цена зашла в целевой диапазон
                        if execution_price < trigger_min and trigger_min <= current_price < trigger_max:
                            self.moving_stop_los(
                                figi=pos_figi,
                                tiker=current_tiker,
                                quantity=qty_lots,
                                avg_price=avg_price,  # Было price_rub=avg_price
                                coeff_sl_price=Decimal(str(new_stop_mult)),  # Передаем float (например, 1.0034)
                                schag=schag,
                            )
                            trade_log.info(f"{current_tiker} - ПЕРЕДВИНУЛ СТОП-ЛОС НА ({log_msg})")
                            moved = True
                            break  # Стоп перенесен, переходим к следующей позиции

                    # 4. Если ни одно условие не сработало
                    if not moved:
                        per = round((execution_price - avg_price) * 100 / avg_price, 1) if avg_price != 0 else 0
                        trade_log.info(f"{current_tiker} - СТОП-ЛОС ОСТАЕТСЯ как было. ({per}%)")
                except Exception as e:
                    # Ловим ошибки по каждому тику отдельно, чтобы сбой на одном не ломал проверку всего портфеля
                    system_log.error(f"{current_tiker} - ошибка в обработке позиции внутри resetting_stop_los: {e}")
        except Exception as e:
            system_log.error(f"resetting_stop_los() критическая ошибка: {e}", exc_info=True)
