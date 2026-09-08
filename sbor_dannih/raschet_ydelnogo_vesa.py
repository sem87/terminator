# from dataclasses import dataclass
#
#
# @dataclass
# class TFData:
#     sma10_up: bool
#     sma10_down: bool
#     rsi_up: bool
#     rsi_down: bool
#     rsi: float
#     macd_up: bool
#     macd_down: bool
#     macd: float
#     volume_ratio: float  # относительно среднего
#
#
# @dataclass
# class Ticker:
#     symbol: str
#     day: TFData
#     hour: TFData
#
#
# # Веса внутри таймфрейма (сумма = 1.0)
# W = {
#     "sma": 0.25,
#     "rsi_d": 0.15,
#     "macd_s": 0.20,
#     "macd_d": 0.15,
#     "vol": 0.25,
# }
# W_TF = {"day": 0.6, "hour": 0.4}
#
#
# def score_tf(d: TFData) -> float:
#     s = 0.0
#     s += W["sma"] * (1 if d.sma10_up else (-1 if d.sma10_down else 0))
#     s += W["rsi_d"] * (1 if d.rsi_up else (-1 if d.rsi_down else 0))
#     s += W["macd_s"] * (1 if d.macd > 0 else -1)
#     s += W["macd_d"] * (1 if d.macd_up else (-1 if d.macd_down else 0))
#     v = d.volume_ratio
#     s += W["vol"] * (1 if v > 1.2 else (-1 if v < 0.8 else 0))
#     return s
#
#
# def score_ticker(t: Ticker) -> dict:
#     day_s = score_tf(t.day)
#     hour_s = score_tf(t.hour)
#     total = day_s * W_TF["day"] + hour_s * W_TF["hour"]
#     return {
#         "symbol": t.symbol,
#         "score": total,
#         "day": day_s,
#         "hour": hour_s,
#         "label": verdict(total),
#     }
#
#
# def verdict(score: float) -> str:
#     if score >= 0.6:
#         return "🟢 СИЛЬНО БЫЧИЙ"
#     if score >= 0.3:
#         return "🟡 УМЕРЕННО БЫЧИЙ"
#     if score >= 0.0:
#         return "⚪ СЛАБО БЫЧИЙ"
#     if score >= -0.3:
#         return "🟠 СЛАБО МЕДВЕЖИЙ"
#     return "🔴 МЕДВЕЖИЙ"
#
#
# def rank(tickers: list[Ticker], min_score: float = 0.3) -> list[dict]:
#     results = sorted([score_ticker(t) for t in tickers], key=lambda x: x["score"], reverse=True)
#     return [r for r in results if r["score"] >= min_score]
#
#
# if __name__ == "__main__":
#     tickers = [
#         Ticker(
#             "GMKN",
#             day=TFData(True, False, True, False, 65.6, True, False, 0.5, 1.47),
#             hour=TFData(True, False, False, True, 59.3, False, True, -0.3, 0.53),
#         ),
#         Ticker(
#             "RUAL",
#             day=TFData(True, False, True, False, 56.8, False, True, 0.2, 1.37),
#             hour=TFData(True, False, False, True, 46.4, False, True, -0.1, 0.73),
#         ),
#         Ticker(
#             "SU26225RMFS1",
#             day=TFData(True, False, False, True, 45.8, False, True, 0.1, 1.90),
#             hour=TFData(True, False, False, True, 47.4, True, False, 0.05, 0.33),
#         ),
#     ]
#
#     for r in rank(tickers):
#         print(f"{r['symbol']:12} score={r['score']:+.2f}  {r['label']}")
