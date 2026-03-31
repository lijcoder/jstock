# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票数据统一API
"""

from bisect import bisect_right
from datetime import datetime

from stock import models
from stock.stock_ths import THSClient
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
        self._ths = None

    @property
    def xq(self) -> XueqiuClient:
        if self._xq is None:
            self._xq = XueqiuClient()
        return self._xq

    @property
    def ths(self) -> THSClient:
        if self._ths is None:
            self._ths = THSClient()
        return self._ths

    def quote(self, symbol: str, market: str = None) -> StockQuote:
        return self.xq.quote(symbol, market)

    def kline(self, symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
        # 获取K线数据（使用同花顺）
        kdata = self.ths.kline(symbol, market, start, end)
        if not kdata.records:
            return kdata
        
        # 获取股本历史（使用雪球，包含所有日期的股本变动）
        shares_data = self.xq.shares(symbol, market)
        if not shares_data.records:
            return kdata
        
        # 按日期排序的股本列表
        dates = [r.chg_date for r in shares_data.records]
        float_shares = [r.float_shares_ashare for r in shares_data.records]
        
        # 为每条K线计算换手率
        for record in kdata.records:
            if record.timestamp and record.volume:
                # 找到 <= record.timestamp 的最近股本
                pos = bisect_right(dates, record.timestamp) - 1
                if pos >= 0 and float_shares[pos]:
                    record.turnover = round(record.volume / float_shares[pos] * 100, 4)
        
        return kdata

    def bonus(self, symbol: str, market: str = None) -> BonusHistory:
        return self.xq.bonus(symbol, market)

    def shares(self, symbol: str, market: str = None) -> SharesHistory:
        return self.xq.shares(symbol, market)


# ============ 主程序 ============
if __name__ == "__main__":
    api = StockAPI()
    print("测试股票统一API")
    print("=" * 50)
    q = api.quote("601398")
    print(f"行情: {q.symbol} {q.name}: {q.current} ({q.percent:+.2f}%)")
    k = api.kline("601398", start="2026-01-01", end="2026-03-31")
    print(f"K线: {k.symbol} 共 {len(k.records)} 条")
    print(f"{'日期':<12} {'收盘':>8} {'成交量':>12} {'流通股本':>14} {'换手率':>8}")
    for r in k.records[-10:]:
        vol = f"{r.volume/1e8:.2f}亿" if r.volume else "N/A"
        turnover = f"{r.turnover:.4f}%" if r.turnover else "N/A"
        print(f"{r.timestamp:<12} {r.close:>8.2f} {vol:>12} {turnover:>14}")
