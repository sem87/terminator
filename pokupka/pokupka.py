import os
from log.logicuber import system_log, debug_log, trade_log
from dotenv import load_dotenv
from t_tech.invest import InstrumentIdType ,InstrumentIdType,OrderDirection,OrderType,OrderExecutionReportStatus,RequestError # Добавлен необходимый импорт
import time
import uuid
load_dotenv("../terminator/.env.term")


def _quotation_to_float(quotation) -> float:
    """Безопасная конвертация объекта Quotation в float"""
    return float(quotation.units) + float(quotation.nano) / 1_000_000_000


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


    # def activ_pokupka(self, figi: str, tiker: str):
    #     """ПОКУПКА АКТИВА, РАССТОНОВКА СТОП-ЛОСА И ТЕЙК-ПРОФИТА"""
    #     try:
    #         # УСЛОВИЯ
    #         if tiker in self.already_exist():
    #             """ПРОВЕРКА КУПЛЕН УЖЕ АКТИВ ИЛИ НЕТ"""
    #             trade_log.info(f"{tiker} - УЖЕ КУПЛЕНО")
    #         else:
    #             """ПОКУПАЕМ ПО ЛУЧШЕЙ ЦЕНЕ КОТОРАЯ ЕСТЬ НА РЫНКЕ"""
    #             # Расчет кол-ва лотов
    #             quantity = self.calculation_number_lots(figi=figi, tiker=tiker)
    #             if quantity <= 0:
    #                 trade_log.info(f"НЕ КУПИЛИ - {tiker} . т.к. можно купить {quantity} шт")
    #                 """НАЧАЛО САМОЙ ПОКУПКИ"""
    #             else:
    #                 try:
    #                     # Покупаем
    #                     self.client.orders.post_order(order_id="",figi=figi,quantity=quantity,
    #                         account_id=self.account_id,
    #                         direction=OrderDirection.ORDER_DIRECTION_BUY,  # на продажу SELL
    #                         order_type=OrderType.ORDER_TYPE_MARKET,)
    #                     debug_log.info(f"КУПИЛ - {tiker} . В КОЛИЧЕСТВЕ {quantity}")
    #                 except RequestError as e:
    #                     system_log.info(f"{tiker} - BuySellAktiv activ_pokupka() RequestError : {e}")
    #                     # Специальная обработка для ошибки 30015
    #                     if e.details == 30015:
    #                         system_log.info(f"{tiker} - BuySellAktiv Некорректное количество лотов: {quantity} шт. Ошибка 30015")
    #                 except Exception as e:
    #                     system_log.info(f"{tiker} - BuySellAktiv activ_pokupka() ошибка в выставлении пост ордера: Exception as e : {e}")
    #                 """КОНЕЦ САМОЙ ПОКУПКИ"""
    #                 time.sleep(25)  # Нужно чтобы прогрузилась покупка. ВЫЯСНИТЬ МИНИМУМ ПРОГРУЗКИ



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
            try:
                # print(f"ОРДЕРА figi {figi} кол-во{quantity}  id - {self.account_id}  ордер {order_id}")
                # 4. ВЫСТАВЛЕНИЕ РЫНОЧНОГО ОРДЕРА НА ПОКУПКУ
                # self.client.orders.post_order(
                #     instrument_id=figi,
                #     id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                #     quantity=quantity,
                #     account_id=self.account_id,
                #     direction=OrderDirection.ORDER_DIRECTION_BUY,
                #     order_type=OrderType.ORDER_TYPE_MARKET,
                #     order_id=order_id, # order_id
                # )

                try:


                    response = self.services.orders.post_order(
                        figi=figi,
                        quantity=quantity,
                        direction=OrderDirection.ORDER_DIRECTION_BUY,
                        order_type=OrderType.ORDER_TYPE_MARKET,
                        account_id=self.account_id,  # Убедись, что ты передаешь это при создании BuySellAktiv
                        order_id=order_id
                    )

                    print(f"Ответ: {response}")
                    trade_log.warning(f"ОРДЕР ВЫСТАВЛЕН - {tiker}. Кол-во: {quantity}")

                except AttributeError:
                    print("Метод post_order не найден в client")
                    print(f"Доступные методы: {[m for m in dir(self.client) if not m.startswith('_')]}")

                except Exception as e:
                    print(f"Ошибка: {e}")
                    trade_log.error(f"Ошибка ордера {tiker}: {e}")


                # trade_log.warning(f"ОРДЕР ВЫСТАВЛЕН - {tiker}. Кол-во: {quantity}")
                # time.sleep(25)



                # # 5.=====НАЧАЛО ОПРОС СТАТУСА ОРДЕРА (вместо time.sleep(25)) =======
                # max_wait_time = 25  # максимальное время ожидания в секундах
                # poll_interval = 2  # интервал опроса в секундах
                # start_time = time.time()
                # is_filled = False
                # while time.time() - start_time < max_wait_time:
                #     order_state = self.client.orders.get_order_state(
                #         account_id=self.account_id,
                #         order_id=order_id)
                #     status = order_state.execution_report_status
                #     # Ордер исполнен или частично исполнен
                #     if status in (
                #             OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL,
                #             OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_PARTIALLYFILL):
                #         debug_log.info(f"ОРДЕР ИСПОЛНЕН - {tiker}. Статус: {status}")
                #         is_filled = True
                #         break
                #     # Ордер отклонён биржей или брокером
                #     elif status == OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_REJECTED:
                #         system_log.error(
                #             f"ОРДЕР ОТКЛОНЁН - {tiker}. Причина: {getattr(order_state, 'message', 'Неизвестно')}")
                #         break
                #     # Ждём перед следующей проверкой
                #     time.sleep(poll_interval)
                # if not is_filled:
                #     system_log.warning(
                #         f"ОРДЕР НЕ ИСПОЛНЕН за {max_wait_time} сек - {tiker}. Проверьте статус вручную.")
                # # 5.=====КОНЕЦ ОПРОС СТАТУСА ОРДЕРА (вместо time.sleep(25)) =======




            # except RequestError as e:
            #     system_log.info(f"{tiker} - BuySellAktiv activ_pokupka() RequestError: {e}")
            #     if e.details == 30015:
            #         system_log.info(f"{tiker} - Некорректное количество лотов: {quantity} шт. Ошибка 30015")
            except Exception as e:
                system_log.info(f"{tiker} - BuySellAktiv activ_pokupka() ошибка в выставлении ордера: {e}")
        except Exception as e:
            system_log.error(f"Критическая ошибка в activ_pokupka для {tiker}: {e}")






                    # """ИНФОРМАЦИЯ О ПОЗИЦИИ НА СЧЕТЕ.ЗА СКОЛЬКО КУПИЛИ И ЛОТНОСТЬ"""
                    # # Получаем информацию о позициях на счёте
                    # positions = cl.operations.get_portfolio(account_id=accid).positions
                    # # Ищем нужный инструмент по FIGI
                    # for position in positions:
                    #     if position.figi == figi:
                    #         average_price = position.average_position_price  # Средняя цена покупки (MoneyValue)
                    #         quantity_lots = position.quantity_lots  # Количество лотов (Decimal)
                    #         # Конвертируем MoneyValue в Decimal
                    #         price_rub = Decimal(average_price.units + average_price.nano / 1e9)
                    #         quantity_lots_new = int(quantity_lots.units + quantity_lots.nano / 1e9)  # переделать
                    #         """КОНЕЦ ИНФОРМАЦИИ О ПОЗИЦИИ НА СЧЕТЕ.ЗА СКОЛЬКО КУПИЛИ И ЛОТНОСТЬ"""
                    #         time.sleep(2)
                    #         schag = opredelaem_schag(cl=cl, figi=figi, tiker=tiker)



                            # """НАЧАЛО ТЕЙК-ПРОФИТ ЗАЯВКИ"""  # продажа при достижении take_profit_price
                            # coeff_take_profit_price = Decimal(1.05)
                            # cl.stop_orders.post_stop_order(
                            #     figi=figi,
                            #     quantity=quantity_lots_new,  # Количество лотов
                            #     price=decimal_to_quotation(
                            #         ((price_rub * coeff_take_profit_price) / schag).quantize(
                            #             Decimal("1"), rounding=ROUND_HALF_UP
                            #         )
                            #         * schag
                            #     ),
                            #     stop_price=decimal_to_quotation(
                            #         ((price_rub * coeff_take_profit_price) / schag).quantize(
                            #             Decimal("1"), rounding=ROUND_HALF_UP
                            #         )
                            #         * schag
                            #     ),
                            #     # Стоп-цена заявки за 1 инструмент
                            #     direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                            #     account_id=accid,
                            #     expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
                            #     stop_order_type=StopOrderType.STOP_ORDER_TYPE_TAKE_PROFIT,
                            # )  # STOP_ORDER_TYPE_STOP_LIMIT    ИЛИ  STOP_ORDER_TYPE_STOP_LOSS
                            # # instrument_id = StopOrdersService
                            # inform.info(
                            #     f"ТЕЙК-ПРОФИТ-{tiker}->ЦЕН{round((price_rub * coeff_take_profit_price / schag) * schag, 3)}"
                            #     f" В КОЛИЧЕСТВЕ {quantity_lots_new}"
                            # )
                            # """КОНЕЦ ТЕЙК-ПРОФИТ ЗАЯВКИ"""
                            # """НАЧАЛО СТОП-ЛОСС ЗАЯВКИ"""
                            # # Стоп-лимит заявка (продажа при достижении take_profit_price)
                            # coeff_stop_loss_price = Decimal(0.9966)  # СДЕЛАЕМ W/R 1:1 (0,34%)
                            # cl.stop_orders.post_stop_order(
                            #     figi=figi,
                            #     quantity=quantity_lots_new,  # Количество лотов
                            #     price=decimal_to_quotation(
                            #         ((price_rub * coeff_stop_loss_price) / schag).quantize(
                            #             Decimal("1"), rounding=ROUND_HALF_UP
                            #         )
                            #         * schag
                            #     ),
                            #     stop_price=decimal_to_quotation(
                            #         ((price_rub * coeff_stop_loss_price) / schag).quantize(
                            #             Decimal("1"), rounding=ROUND_HALF_UP
                            #         )
                            #         * schag
                            #     ),
                            #     # Стоп-цена заявки за 1 инструмент/
                            #     direction=StopOrderDirection.STOP_ORDER_DIRECTION_SELL,
                            #     account_id=accid,
                            #     expiration_type=StopOrderExpirationType.STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL,
                            #     stop_order_type=StopOrderType.STOP_ORDER_TYPE_STOP_LOSS,
                            # )  # STOP_ORDER_TYPE_STOP_LIMIT    ИЛИ  STOP_ORDER_TYPE_STOP_LOSS
                            # inform.info(
                            #     f"СТОП-ЛИМИТ-{tiker}->ЦЕНА {round((price_rub * coeff_stop_loss_price / schag) * schag, 3)}"
                            #     f" В КОЛИЧЕСТВЕ {quantity_lots_new}"
                            # )
                            # """КОНЕЦ СТОП-ЛОСС ЗАЯВКИ"""
        #             """КОНЕЦ РАСЧИТАЕМ И ВЫСТАВИМ СТОП-ЛОСС И ТЕЙК-ПРОФИТ"""
        # except Exception as e:
        #     system_log.info(f"{tiker} - BuySellAktiv  activ_pokupka() ошибка при покупки актива : Exception as e : {e}")




