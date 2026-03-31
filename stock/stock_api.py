# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票数据统一API
"""

from stock import models
from stock.stock_xq import XueqiuClient

__all__ = ['quote', 'kline', 'bonus', 'shares', 'StockAPI']

StockQuote = models.StockQuote
BonusHistory = models.BonusHistory
SharesHistory = models.SharesHistory
KlineData = models.KlineData


# ============ 便捷函数 ============
_api = None


def _get_api():
    global _api
    if _api is None:
        _api = StockAPI()
    return _api


def quote(symbol: str, market: str = None) -> StockQuote:
    return _get_api().quote(symbol, market)


def kline(symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
    return _get_api().kline(symbol, market, start, end)


def bonus(symbol: str, market: str = None) -> BonusHistory:
    return _get_api().bonus(symbol, market)


def shares(symbol: str, market: str = None) -> SharesHistory:
    return _get_api().shares(symbol, market)


# ============ 主类 ============
class StockAPI:
    """股票数据统一API"""

    def __init__(self):
        self._xq = None

    @property
    def xq(self) -> XueqiuClient:
        if self._xq is None:
            self._xq = XueqiuClient()
        return self._xq

    def quote(self, symbol: str, market: str = None) -> StockQuote:
        return self.xq.quote(symbol, market)

    def kline(self, symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
        return self.xq.kline(symbol, market, start, end)

    def bonus(self, symbol: str, market: str = None) -> BonusHistory:
        return self.xq.bonus(symbol, market)

    def shares(self, symbol: str, market: str = None) -> SharesHistory:
        return self.xq.shares(symbol, market)


# ============ 主程序 ============
if __name__ == "__main__":
    api = StockAPI()
    print("测试股票统一API")
    print("=" * 40)
    q = api.quote("601398")
    print(f"行情: {q.symbol} {q.name}: {q.current} ({q.percent:+.2f}%)")
    k = api.kline("601398", start="2025-01-01")
    print(f"K线: {k.symbol} 共 {len(k.records)} 条")
