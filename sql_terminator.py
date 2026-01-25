from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Float, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, backref, mapped_column, relationship, sessionmaker
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, asc

engine = create_engine('sqlite:///sql_terminator.db')  # echo=True

# Переименуйте переменную, чтобы избежать конфликта имен
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()  # Используйте переименованную переменную


class Base(DeclarativeBase):
    pass


#
# class Errors(Base):
#     __tablename__ = 'errors'
#     # Без nullable=True для primary_key (по False)
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, name="Id")
#     time_data: Mapped[str] = mapped_column(String, name="Время")  # Время
#     tiker: Mapped[str] = mapped_column(String, name="Тикер")
#     error: Mapped[str] = mapped_column(String, name="Ошибка")
#     description: Mapped[str] = mapped_column(String, name="Описание")


class SalesInform(Base):
    """ИНФОРМАЦИЮ О ПРОДАЖЕ И ЗАПИСЫВАЕТ В SQL salesinform"""
    __tablename__ = 'salesinform'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date_sale: Mapped[datetime] = mapped_column(DateTime)
    tiker: Mapped[str] = mapped_column(String)
    operatio_type: Mapped[str] = mapped_column(String)
    quantity_sale: Mapped[int] = mapped_column(Integer)
    sale_price: Mapped[float] = mapped_column(Float)
    commission_sales: Mapped[float] = mapped_column(Float)
    figi: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint('tiker', 'date_sale', 'sale_price'),)


class BuyBase(Base):
    """ОБЩИЙ КЛАСС (абстрактный). ИНФОРМАЦИЮ О ПРОДАЖЕ И ЗАПИСЫВАЕТ В SQL"""
    __abstract__ = True  # Это не создаст отдельную таблицу
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date_buy: Mapped[datetime] = mapped_column(DateTime)
    tiker: Mapped[str] = mapped_column(String)
    operatio_type: Mapped[str] = mapped_column(String)
    quantity_buy: Mapped[int] = mapped_column(Integer)
    buy_price: Mapped[float] = mapped_column(Float)
    commission_buy: Mapped[float] = mapped_column(Float)
    figi: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint('tiker', 'date_buy', 'buy_price'),)


class BuyInform(BuyBase):
    """ИНФОРМАЦИЮ О ПРОДАЖЕ И ЗАПИСЫВАЕТ В SQL ДЛЯ FIFO. ВСЕ ОБРАБОТАННОЕ КОЛ-ВО = 0 """
    __tablename__ = 'buyinform'


class ArchiveBuyInform(BuyBase):
    """ИНФОРМАЦИЮ О ПРОДАЖЕ И ЗАПИСЫВАЕТ В SQL ДЛЯ АРХИВА."""
    __tablename__ = 'archivebuyinform'


class MyTradeResult(Base):
    __tablename__ = 'mytrade_results'
    id = Column(Integer, primary_key=True)
    tiker: Mapped[str] = mapped_column(String)
    date_sale: Mapped[datetime] = mapped_column(DateTime)
    quantity_sale: Mapped[int] = mapped_column(Integer)  # Количество продажи и равно кол-ву покупки
    buy_price: Mapped[float] = mapped_column(Float)
    commission_buy: Mapped[float] = mapped_column(Float)
    sale_price: Mapped[float] = mapped_column(Float)
    commission_sales: Mapped[float] = mapped_column(Float)
    income: Mapped[float] = mapped_column(Float)
    # ---Выводы---
    conclusion_trading: Mapped[str] = mapped_column(String)  # Выводы о продажи
    net_profit: Mapped[float] = mapped_column(Float)  # Чистая прибыль (-13%)
    percent_profit: Mapped[float] = mapped_column(Float)  # % заработка
    time_difference_days: Mapped[int] = mapped_column(Integer)  # Разница времени дни
    # ---Для справки---
    figi: Mapped[str] = mapped_column(String)
    date_buy: Mapped[datetime] = mapped_column(DateTime)


class FilterTickerDict(Base):
    """ИНФОРМАЦИЮ О ПРОДАЖЕ И ЗАПИСЫВАЕТ В SQL salesinform"""
    __tablename__ = 'filter_ticker_dict'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    tiker: Mapped[str] = mapped_column(String)
    timeframe: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    strategy: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)


class AnalysisTiker(Base):
    """ИНФОРМАЦИЮ О ПРОДАЖЕ И ЗАПИСЫВАЕТ В SQL salesinform"""
    __tablename__ = 'analysis_tiker'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tiker: Mapped[str] = mapped_column(String)
    price_mean: Mapped[str] = mapped_column(String)
    volume_mean: Mapped[str] = mapped_column(String)
    trade_sphere: Mapped[str] = mapped_column(String)
    activity: Mapped[str] = mapped_column(String)
    statistics: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)


Base.metadata.create_all(bind=engine)
