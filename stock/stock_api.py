# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票数据统一API - 门面模式
"""

from stock import models
from stock.stock_xq import XueqiuClient

# 导出
__all__ = ['quote', 'kline', 'bonus', 'shares', 'StockAPI']

StockQuote = models.StockQuote
BonusHistory = models.BonusHistory
SharesHistory = models.SharesHistory
KlineData = models.KlineData


# ============ 便捷函数 ============
_api = None


def _get_api() -> 'StockAPI':
    global _api
    if _api is None:
        _api = StockAPI()
    return _api


def quote(symbol: str, market: str = None) -> StockQuote:
    """获取股票行情"""
    return _get_api().quote(symbol, market)


def kline(symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
    """获取K线数据"""
    return _get_api().kline(symbol, market, start, end)


def bonus(symbol: str, market: str = None) -> BonusHistory:
    """获取分红历史"""
    return _get_api().bonus(symbol, market)


def shares(symbol: str, market: str = None) -> SharesHistory:
    """获取股本变动"""
    return _get_api().shares(symbol, market)


# ============ 主类 ============
class StockAPI:
    """
    股票数据统一API - 门面类
    
    使用示例：
        from stock import StockAPI, quote, kline, bonus, shares
        
        api = StockAPI()
        
        q = api.quote("601398")
        k = api.kline("601398")
        k = api.kline("601398", market="SH", start="2025-01-01", end="2025-12-31")
    """

    def __init__(self):
        self._xq = None

    @property
    def xq(self) -> XueqiuClient:
        if self._xq is None:
            self._xq = XueqiuClient()
        return self._xq

    def quote(self, symbol: str, market: str = None) -> StockQuote:
        """获取股票行情"""
        return self.xq.quote(symbol, market)

    def kline(self, symbol: str, market: str = None, start: str = None, end: str = None) -> KlineData:
        """
        获取日K线数据
        
        :param symbol: 股票代码，如 601398、SH601398
        :param market: 市场，SH/SZ，默认自动判断
        :param start: 开始日期 YYYY-MM-DD，默认最近1年
        :param end: 结束日期 YYYY-MM-DD，默认今天
        """
        return self.xq.kline(symbol, market, start, end)

    def bonus(self, symbol: str, market: str = None) -> BonusHistory:
        """获取分红历史"""
        return self.xq.bonus(symbol, market)

    def shares(self, symbol: str, market: str = None) -> SharesHistory:
        """获取股本变动"""
        return self.xq.shares(symbol, market)


# ============ 主程序 ============
if __name__ == "__main__":
    api = StockAPI()

    print("=" * 50)
    print("测试股票统一API")
    print("=" * 50)

    # 行情
    print("\n📊 行情:")
    q = api.quote("601398")
    print(f"  {q.symbol} {q.name}: {q.current} ({q.percent:+.2f}%)")

    # K线
    print("\n📈 K线:")
    k = api.kline("601398", start="2025-01-01", end="2025-12-31")
    print(f"  {k.symbol} 共 {len(k.records)} 条")
    for r in k.records[:3]:
        print(f"    {r.timestamp}: {r.close}")

    print("\n✅ 完成")
