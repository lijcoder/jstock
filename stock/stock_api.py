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
from stock.stock_ths import daily_kline as ths_daily_kline, KlineData as THSKlineData

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


def kline(
    symbol: str,
    period: str = "day",
    years: int = 5,
    start: str = None,
    end: str = None,
    market: str = None,
) -> KlineData:
    """获取K线数据"""
    return _get_api().kline(symbol, period=period, years=years, start=start, end=end, market=market)


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
        
        # 获取K线 - 最近5年
        k = api.kline("601398", years=5)
        
        # 获取K线 - 日期范围
        k = api.kline("601398", start="2025-01-01", end="2025-12-31")
        
        # 月K线 - 最近2年
        k = api.kline("601398", period="month", years=2)
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

    def kline(
        self,
        symbol: str,
        period: str = "day",
        years: int = 5,
        start: str = None,
        end: str = None,
        market: str = None,
    ) -> KlineData:
        """
        获取K线数据
        
        :param symbol: 股票代码
        :param period: 周期，day/week/month/quarter/year，默认 day
        :param years: 最近N年，默认 5
        :param start: 开始日期，YYYY-MM-DD 格式
        :param end: 结束日期，YYYY-MM-DD 格式
        :param market: 指定市场
        
        使用示例:
            kline("601398", years=5)           # 最近5年
            kline("601398", start="2025-01-01", end="2025-12-31")  # 2025全年
            kline("601398", period="month")     # 月K线，默认最近5年
        """
        # 规范化代码
        raw_symbol = symbol
        symbol = normalize_symbol(symbol, market)
        market = symbol[:2]
        
        # 调用数据源
        if self.primary == "xq":
            return self.xq.kline(symbol, period, years, start, end)
        
        # THS fallback
        return ths_kline(raw_symbol, market, years, start, end)


def ths_kline(
    code: str,
    market: str,
    years: int = 5,
    start: str = None,
    end: str = None,
) -> KlineData:
    """
    同花顺K线接口
    
    :param code: 股票代码（纯数字）
    :param market: 市场 "SH" 或 "SZ"
    :param years: 最近N年
    :param start: 开始日期
    :param end: 结束日期
    """
    market_prefix = "sh" if market == "SH" else "sz"
    
    # THS只支持日K和日期范围
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

    # 最近5年
    print("\n📈 最近5年K线:")
    k = api.kline("601398", years=5)
    print(f"  {k.symbol} 共 {len(k.records)} 条")
    if k.records:
        print(f"  从 {k.records[0].timestamp} 到 {k.records[-1].timestamp}")

    # 日期范围
    print("\n📈 2025全年K线:")
    k = api.kline("601398", start="2025-01-01", end="2025-12-31")
    print(f"  {k.symbol} 共 {len(k.records)} 条")
    if k.records:
        print(f"  从 {k.records[0].timestamp} 到 {k.records[-1].timestamp}")

    # 月K线
    print("\n📈 最近2年月K线:")
    k = api.kline("600519", period="month", years=2)
    print(f"  {k.symbol} 共 {len(k.records)} 条")
    for r in k.records[-6:]:
        print(f"    {r.timestamp}: 收={r.close}")

    print("\n✅ 完成")
