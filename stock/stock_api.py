# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票数据统一API - 门面模式
自动选择数据源，调用方无需关心底层实现
"""

from typing import Optional

from stock import models
from stock.stock_xq import XueqiuClient, normalize_symbol
from stock.stock_ths import daily_kline as ths_daily_kline

# 导出统一的数据模型
__all__ = [
    'quote',
    'kline',
    'bonus',
    'shares',
    'StockAPI',
]
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


def kline(symbol: str, start: str = None, end: str = None, market: str = None) -> KlineData:
    """获取K线数据（日K）"""
    return _get_api().kline(symbol, start=start, end=end, market=market)


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
        
        # 获取行情
        q = api.quote("601398")
        print(q.name, q.current)
        
        # 获取日K线
        k = api.kline("601398")                      # 默认最近1年
        k = api.kline("601398", end="2026-03-31")    # 到指定日期
        k = api.kline("601398", start="2025-01-01")  # 从指定日期至今
        k = api.kline("601398", start="2025-01-01", end="2025-12-31")  # 日期范围
    """

    def __init__(self, primary: str = "xq"):
        """
        初始化
        
        :param primary: 首选数据源，"xq" 或 "ths"
        """
        self.primary = primary
        self._xq = None

    @property
    def xq(self) -> XueqiuClient:
        """雪球客户端（延迟初始化）"""
        if self._xq is None:
            self._xq = XueqiuClient()
        return self._xq

    def quote(self, symbol: str, market: str = None) -> StockQuote:
        """获取股票行情"""
        symbol = normalize_symbol(symbol, market)
        return self.xq.stock_quote(symbol)

    def bonus(self, symbol: str, market: str = None) -> BonusHistory:
        """获取分红历史"""
        symbol = normalize_symbol(symbol, market)
        return self.xq.stock_bonus(symbol)

    def shares(self, symbol: str, market: str = None) -> SharesHistory:
        """获取股本变动"""
        symbol = normalize_symbol(symbol, market)
        return self.xq.stock_shares(symbol)

    def kline(self, symbol: str, start: str = None, end: str = None, market: str = None) -> KlineData:
        """
        获取日K线数据
        
        :param symbol: 股票代码
        :param start: 开始日期，YYYY-MM-DD 格式
        :param end: 结束日期，YYYY-MM-DD 格式
        :param market: 指定市场
        
        使用示例:
            kline("601398")                           # 默认最近1年
            kline("601398", end="2026-03-31")         # 到指定日期
            kline("601398", start="2025-01-01")       # 从指定日期至今
            kline("601398", start="2025-01-01", end="2025-12-31")  # 日期范围
        """
        # 规范化代码
        raw_symbol = symbol
        symbol = normalize_symbol(symbol, market)
        market = symbol[:2]
        
        # 调用数据源
        if self.primary == "xq":
            return self.xq.kline(symbol, start, end)
        
        # THS fallback
        return ths_kline(raw_symbol, market, start, end)


def ths_kline(code: str, market: str, start: str = None, end: str = None) -> KlineData:
    """同花顺K线接口"""
    market_prefix = "sh" if market == "SH" else "sz"
    
    data = ths_daily_kline(code, market_prefix)
    
    # 过滤日期范围
    if start or end:
        data = _filter_kline_by_date(data, start, end)
    
    return data


def _filter_kline_by_date(data: KlineData, start: str = None, end: str = None) -> KlineData:
    """按日期过滤K线数据"""
    from datetime import datetime
    
    if not data.records:
        return data
    
    records = data.records
    
    if start:
        start_dt = datetime.strptime(start, "%Y-%m-%d").date()
        records = [r for r in records if r.timestamp and datetime.strptime(r.timestamp, "%Y-%m-%d").date() >= start_dt]
    
    if end:
        end_dt = datetime.strptime(end, "%Y-%m-%d").date()
        records = [r for r in records if r.timestamp and datetime.strptime(r.timestamp, "%Y-%m-%d").date() <= end_dt]
    
    return KlineData(symbol=data.symbol, period=data.period, records=records)


# ============ 主程序 ============
if __name__ == "__main__":
    api = StockAPI()

    print("=" * 50)
    print("测试股票统一API - K线接口")
    print("=" * 50)

    # 默认最近1年
    print("\n📈 默认最近1年:")
    k = api.kline("601398")
    print(f"  {k.symbol} 共 {len(k.records)} 条")
    if k.records:
        print(f"  从 {k.records[0].timestamp} 到 {k.records[-1].timestamp}")

    # 到指定日期
    print("\n📈 到指定日期:")
    k = api.kline("601398", end="2025-12-31")
    print(f"  {k.symbol} 共 {len(k.records)} 条")

    # 从指定日期至今
    print("\n📈 从指定日期至今:")
    k = api.kline("601398", start="2025-01-01")
    print(f"  {k.symbol} 共 {len(k.records)} 条")

    # 日期范围
    print("\n📈 日期范围:")
    k = api.kline("601398", start="2025-01-01", end="2025-12-31")
    print(f"  {k.symbol} 共 {len(k.records)} 条")

    print("\n✅ 完成")
